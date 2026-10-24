# Deployment

## Contents

- [Repository-supported deployment artifacts](#repository-supported-deployment-artifacts)
- [Runtime and external prerequisites](#runtime-and-external-prerequisites)
- [Production configuration](#production-configuration)
- [Migrations and application startup](#migrations-and-application-startup)
- [Health and operational checks](#health-and-operational-checks)
- [Networking and storage considerations](#networking-and-storage-considerations)
- [Release and rollback considerations](#release-and-rollback-considerations)

## Repository-supported deployment artifacts

The backend includes a [`Dockerfile`](../Dockerfile) and [`docker-compose.yml`](../docker-compose.yml). The Dockerfile uses `python:3.12-slim`, installs `requirements.txt`, copies the application/migrations/scripts, switches to a non-root `bunavision` user (UID 10001), exposes port 8000, and starts the Uvicorn app factory. Compose declares a PostgreSQL 17 container and one backend container. There are no Kubernetes/ECS/Elastic Beanstalk manifests, Terraform/CloudFormation resources, production URLs, TLS proxy configuration, or deployment pipeline in this backend directory.

## Runtime and external prerequisites

The project metadata declares Python `>=3.11`; the checked-in image uses Python 3.12. Production needs:

- PostgreSQL reachable using `DATABASE_URL`; the schema must be migrated before the Dockerfile's normal startup command.
- A reachable Vision HTTP service at `VISION_SERVICE_URL`.
- A valid Gemini API key and currently available `GEMINI_MODEL` for the advisory step.
- An image store. `memory` is ephemeral and returns non-browser-fetchable URLs. Use `s3` for durable image access.
- If S3 is used: `S3_BUCKET`, `S3_REGION`, network access, AWS credentials from the default credential chain, and an appropriately private bucket.

There is an unresolved backend/Vision response-schema mismatch in the checked-in source. Do not infer integrated inference readiness from successful backend startup; see [Vision integration](vision-integration.md#source-level-contract-mismatch). No live deployment or production configuration was verified during this documentation task.

## Production configuration

Set the required application variables from [configuration](configuration.md#application-settings): `VISION_SERVICE_URL`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `IMAGE_STORE`, `DATABASE_URL`, and `JWT_SECRET`. For production, use `IMAGE_STORE=s3`, provide bucket/region and secure AWS credentials, set actual frontend origins in `CORS_ALLOWED_ORIGINS`, and review the provisional quota/image values against expected use. The app accepts HTTP Vision URLs; TLS and private networking must be arranged outside this code.

Do not use example credentials from `.env.example` outside disposable local development. Compose also requires `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` in its interpolation environment; those are Compose variables, not application settings.

## Migrations and application startup

The image's command is:

```sh
uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```

The Dockerfile explicitly treats `alembic upgrade head` as a separate release step. Run that command once against the target database before starting new application containers. On startup, `build_services()` checks PostgreSQL connectivity by selecting `users.user_id` and `assessments.assessment_id`. This is not an Alembic revision/head check and cannot guarantee every schema column is current. Vision/Gemini connectivity is not checked at startup.

The checked-in Compose backend command instead runs `alembic upgrade head` and then Uvicorn in the same container. Compose sets its own `DATABASE_URL` pointing at service `db` and overrides `VISION_SERVICE_URL` with `http://host.docker.internal:9000`. You must add `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` to `.env` for Compose interpolation, supply the other required backend settings, and run Vision separately. The Compose file has basic `depends_on` startup ordering but no database health check. It also has no backend healthcheck declaration.

For a local Compose build, from `backend/`:

```sh
cp .env.example .env
# Edit .env: set required Gemini/JWT values and add POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB.
docker compose up --build
```

This command will fail its backend command if PostgreSQL is not ready when Alembic connects or if Vision/Gemini settings are missing/invalid. Host resolution for `host.docker.internal` depends on the Docker platform; Compose does not add a Linux host-gateway mapping.

## Health and operational checks

`GET /health` is an unauthenticated liveness check returning `{"status":"ok","version":"0.4.0"}`. It does not establish readiness of PostgreSQL, Vision, Gemini, or S3. PostgreSQL is checked during startup; other services are checked only when a workflow invokes them. Monitor application logs and dependency-specific metrics outside this backend; no metrics exporter is implemented here.

Admin diagnostics expose persisted outcomes at `/api/v1/admin/overview`, failed attempts and filters at `/api/v1/admin/assessments`, model/validator usage at `/api/v1/admin/model-versions`, and active configured limits at `/api/v1/admin/limits`. These routes require an admin bearer token. Values from `/limits` are settings, not measured throughput or capacity.

## Networking and storage considerations

**Repository facts:** the API listens on port 8000 in the image. Vision defaults to a host service on port 9000 in Compose. The backend's S3 adapter uses boto3's default credential chain and creates expiring GET presigned URLs. The app allows only configured CORS origins and does not enable CORS when the list is empty.

**Deployment recommendations (not provisioned by this repository):** terminate public TLS at a trusted proxy; keep PostgreSQL and Vision on private networks; ensure proxy/body limits permit the configured image size plus 64 KiB; set upstream timeouts to accommodate Vision, Gemini, database, and storage latency; use a private S3 bucket, least-privilege IAM role, and any required encryption/lifecycle policy. Restrict network access to Vision `/reload-model`: the checked-in Vision route has no authentication dependency, even though the backend entry point requires an admin. Presigned URLs are bearer links until expiration.

Each Uvicorn worker/process builds its own service instance and connection pool. The hourly quota's count/insert sequence and the active-assessment semaphore are not globally coordinated. Multiple processes can exceed the configured quota; deployment sizing does not change that fact. See [security](security.md#quotas-and-idempotency).

## Release and rollback considerations

The migration set currently consists of one initial migration. Its downgrade drops `users` and `assessments`, including their data. Do not use `alembic downgrade base` as a routine application rollback. Rollback planning must account for the schema version already applied and compatibility of old application code with it; the repository contains no automated rollback strategy or migration backup tooling. Use database backups and a reviewed release procedure appropriate to the deployment platform.
