# BunaVision backend

BunaVision's Python API accepts green coffee sample photos, asks the separately deployed Vision service to screen them, obtains a bilingual advisory from Gemini, stores assessment metadata in PostgreSQL and images in the configured image store, and serves owner-scoped history. Results are preliminary model predictions. The API does not issue an official ECX or SCA grade and does not contain computer-vision code.

## Contents

- [Quick start](#quick-start)
- [Responsibilities and layout](#responsibilities-and-layout)
- [Implemented behavior and limitations](#implemented-behavior-and-limitations)
- [Documentation](#documentation)

## Quick start

The repository declares Python `>=3.11`; the container image uses Python 3.12. You also need PostgreSQL, a reachable Vision HTTP service, and Gemini credentials/model configuration for assessment requests. The API checks PostgreSQL connectivity and probes its user/assessment tables at startup, but it does not compare the database's Alembic revision or check Vision/Gemini availability until a request needs them.

1. Create the local settings file and fill in the required values described in [configuration](docs/configuration.md). `.env.example` is a template, not a ready-to-run secret file.

   ```sh
   cp .env.example .env
   ```

   Set `GEMINI_API_KEY`, `GEMINI_MODEL`, `JWT_SECRET` (at least 32 characters), and a `VISION_SERVICE_URL` reachable from this machine. `DATABASE_URL` in the template matches the local database command below. `IMAGE_STORE=memory` is suitable for a local API smoke test, but its image URLs are not fetchable by a browser and its objects disappear on restart.

2. Start a local PostgreSQL 17 container. This command uses example-only local credentials; do not reuse them outside a disposable development database.

   ```sh
   docker run --detach --name bunavision-postgres \
     --env POSTGRES_USER=bunavision \
     --env POSTGRES_PASSWORD=change-me \
     --env POSTGRES_DB=bunavision \
     --publish 5432:5432 postgres:17-alpine
   ```

3. Install the backend and development/test dependencies, then apply the migration.

   ```sh
   python3 -m venv .venv
   . .venv/bin/activate
   python -m pip install -r requirements-dev.txt
   alembic upgrade head
   ```

4. (Optional) Create an administrator. The password is read interactively; it is not accepted as a command-line argument.

   ```sh
   python -m scripts.create_admin --email admin@example.com
   ```

5. Start the API and check its liveness endpoint.

   ```sh
   uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
   curl http://127.0.0.1:8000/health
   ```

   Interactive OpenAPI documentation is served by FastAPI at `/docs`; ReDoc is at `/redoc`, and the schema is at `/openapi.json`.

Run the tests with `python -m pytest`. See [testing](docs/testing.md) for test coverage and the local asyncio runtime finding; do not treat a stalled `asyncio.to_thread` probe as an application test result.

## Responsibilities and layout

The backend owns the versioned public API and workflow orchestration. It owns authentication, upload validation, taxonomy mapping, result normalization, persistence, and presigned image URL creation. Vision detections come only from the HTTP service; Gemini receives derived counts and class coverage, not images or caller-provided text.

| Path | Responsibility |
|---|---|
| `app/api/` | FastAPI factory, routers, request middleware, dependency injection and HTTP error mapping |
| `app/schemas/` | Public Pydantic request and response models |
| `app/services/` | Assessment, auth and admin workflows; adapter ports in `ports.py` |
| `app/domain/` | Domain entities, errors, defect taxonomy and pure summary/limitation rules |
| `app/adapters/` | PostgreSQL, Vision HTTP, Gemini, S3/memory storage and password/token implementations |
| `app/core/` | Typed settings, request-aware logging, IDs and clock |
| `migrations/` | Async Alembic environment and database migrations |
| `scripts/` | Operator admin creation and OpenAPI export |
| `tests/` | Unit tests and mocked adapter/middleware tests |

See [architecture](docs/architecture.md) for request flow and [database](docs/database.md) for stored records.

## Implemented behavior and limitations

- Registration creates regular users. Administrators are created with the operator-run script; there is no HTTP user-management API.
- An assessment is complete only when valid Vision output, a validated Gemini advisory, image handling, and persistence succeed. Dependency failures return an error and are recorded as failed attempts where possible. Invalid images and Vision's non-coffee rejection are not recorded as assessments.
- A detection is one reported defect region/bounding box, not one bean. Zero detections is a valid completed result. The taxonomy currently marks three of thirteen listed defect classes as scanned; unknown Vision labels fail rather than being guessed. No grade or bean total is returned.
- Idempotency is optional and scoped to an owner. Reuse the key with the same bytes to replay a saved result; reusing it with different bytes is rejected. Failed attempts do not retain their key.
- Hourly usage is counted from persisted completed and failed assessments. The same-owner admission guard and active-assessment cap are process-local, so these controls are not globally atomic across multiple API processes.
- The in-memory image store is development/test-only. S3-compatible storage is available through the S3 adapter. The repository includes Docker and Compose configuration, but no production cloud infrastructure or Vision service deployment.
- Integration prerequisite: the backend currently requires coffee-validator response fields that are absent from the checked-in Vision service schema. Live inference compatibility is unverified; see [Vision integration](docs/vision-integration.md#source-level-contract-mismatch) before treating the stack as end-to-end ready.
- The committed public OpenAPI contract also differs from current router behavior on idempotency status/validation and upload-size documentation. See [API reference](docs/api-reference.md#shared-contract-alignment); this backend-only docs change leaves the shared contract untouched.

## Documentation

- [Architecture](docs/architecture.md)
- [API reference](docs/api-reference.md)
- [Configuration](docs/configuration.md)
- [Database](docs/database.md)
- [Vision integration](docs/vision-integration.md)
- [Security](docs/security.md)
- [Testing](docs/testing.md)
- [Deployment](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)
