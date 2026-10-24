# Database and persistence

## Contents

- [Engine and connection](#engine-and-connection)
- [Tables and relationships](#tables-and-relationships)
- [Constraints and indexes](#constraints-and-indexes)
- [Repositories and transaction boundaries](#repositories-and-transaction-boundaries)
- [Assessment persistence lifecycle](#assessment-persistence-lifecycle)
- [Migrations and startup check](#migrations-and-startup-check)
- [Test persistence](#test-persistence)

## Engine and connection

The production container wires asynchronous SQLAlchemy repositories to PostgreSQL through `asyncpg`. The URL is supplied by `DATABASE_URL` in the form `postgresql+asyncpg://.../<database>`. The checked-in Compose file declares `postgres:17-alpine`; no other production database engine or managed database configuration is defined here. PostgreSQL-specific JSONB and partial indexes are used, so the implementation is not database-agnostic in practice.

The SQLAlchemy engine uses `pool_pre_ping=True`, configurable pool size/overflow, and an async session factory with `expire_on_commit=False`. `build_services()` creates one engine and repositories per app process and disposes the engine during shutdown.

## Tables and relationships

The current schema is defined in [`app/adapters/db/postgres/tables.py`](../app/adapters/db/postgres/tables.py) and first created by [`0001_users_and_assessments.py`](../migrations/versions/0001_users_and_assessments.py).

| Table | Columns and purpose |
|---|---|
| `users` | `user_id` UUID primary key; normalized `email`; `password_hash`; `role` (`user` or `admin`); `is_active`; timezone-aware `created_at`. The unique email index applies to the normalized stored value. |
| `assessments` | `assessment_id` text primary key (generated as `asmt_` plus a UUID hex string); `owner_id` UUID foreign key to `users.user_id`; `status`; timezone-aware `created_at`; `processing_time_ms`; `image_sha256`; nullable `idempotency_key`; nullable `error_code`, `model_version`, and `validator_version`; nullable `result` JSONB. |

One user can own many assessment rows. The foreign key uses `ON DELETE RESTRICT`; the application has no user-delete endpoint. The result JSONB contains schema version 1, model and coffee-validator version data, detections (taxonomy key, confidence and pixel box), class coverage, bilingual advisory, and image object keys. It does not contain image bytes or presigned URLs. The summary is recomputed from the stored detections during rehydration, rather than stored as a second count source. See [Vision integration](vision-integration.md#response-mapping) for what a detection means.

Image objects live outside PostgreSQL in the configured image store. When `IMAGE_STORE=s3`, the row contains object keys only. Short-lived URLs are generated when an assessment is returned.

## Constraints and indexes

- `ck_users_role` restricts roles to `user` or `admin`.
- `uq_users_email` uniquely indexes the normalized email.
- `ck_assessments_status` allows only `completed` and `failed`.
- `ck_assessments_status_shape` requires a completed row to have non-null result/model/validator fields and no error code; failed rows require an error code and null result/model/validator fields.
- `ix_assessments_owner_created` supports owner-scoped newest-first listing.
- `ix_assessments_status_created` supports status-oriented operator queries.
- `uq_assessments_owner_idempotency` is a PostgreSQL partial unique index on `(owner_id, idempotency_key)` where the key is not null. Failed attempts do not retain keys.

## Repositories and transaction boundaries

Services depend on `AssessmentRepository`, `AssessmentAdminQueries`, and `UserRepository` protocols declared in `app/services/ports.py`. `PostgresAssessmentRepository` and `PostgresUserRepository` implement them. Database/driver errors are translated to `PersistenceError`; repositories do not expose SQLAlchemy rows through the API.

Each `add()` opens its own SQLAlchemy transaction. User inserts translate an email uniqueness conflict to `EMAIL_ALREADY_REGISTERED`. Assessment insertion translates a conflict on the idempotency index to an internal duplicate-key signal so the service can replay the winning result. Reads use short-lived async sessions. There is no transaction spanning Vision, Gemini, object storage, and PostgreSQL.

The assessment workflow stores image objects and creates URLs before inserting the completed row. If later work fails, it attempts to delete any objects it wrote. Cleanup is best-effort: a deletion failure is logged while the original failure is returned. Dependency failures are recorded as a separate failed assessment row where the database remains available; a failed write is logged and cannot be guaranteed to appear in admin history.

## Assessment persistence lifecycle

1. The service validates the image before allocating the assessment ID. Invalid bytes and Vision's non-coffee rejection do not create rows.
2. Once accepted for processing, a dependency error is associated with the allocated assessment ID and recorded with `status=failed`, elapsed processing time, image hash, and error code, when persistence succeeds.
3. On success, the row is inserted with `status=completed`, result JSONB and model/validator versions. PostgreSQL check constraints enforce the completed/failed shape.
4. An idempotency key is saved only on a completed result. A retry with the same owner, key, and exact bytes returns the previous result; the same key with different bytes is rejected. A failed attempt can be retried with the same key because failed rows store `NULL` for the key.

The hourly quota counts persisted completed and failed attempts. Its count and subsequent insert are not one atomic reservation across processes; see [security](security.md#quotas-and-idempotency).

## Migrations and startup check

From `backend/`, configure `DATABASE_URL` and run:

```sh
alembic upgrade head
alembic current
```

There is one migration (`0001`, users and assessments). `migrations/env.py` uses async Alembic and requires only `DATABASE_URL`. Application startup then runs `SELECT` probes for `users.user_id` and `assessments.assessment_id`. It fails with a configuration error if PostgreSQL cannot be reached or these queries fail. This is a connectivity/basic-schema probe, not a check of the current Alembic revision and not a guarantee that every column matches the latest migration. It does not create tables automatically.

The initial migration's `downgrade()` drops both tables and their data. Treat that downgrade as destructive. The Dockerfile describes migrations as a separate release step. The checked-in Compose service instead runs `alembic upgrade head` in its backend container command before Uvicorn.

## Test persistence

Service and repository tests use `InMemoryAssessmentRepository`, `InMemoryUserRepository`, and hand-written fakes. They do not connect to PostgreSQL or validate SQL constraints, network failures, locking behavior, or migration execution. `tests/unit/test_serialization.py` tests the result JSON serializer separately. There is no database integration-test harness configured in this backend.
