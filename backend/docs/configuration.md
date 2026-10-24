# Configuration reference

## Contents

- [Loading settings](#loading-settings)
- [Application settings](#application-settings)
- [Docker Compose variables](#docker-compose-variables)
- [Startup validation](#startup-validation)

## Loading settings

`app.core.config.Settings` reads environment variables and an optional UTF-8 `.env` file in the process working directory. Environment values take precedence. Unknown settings are ignored. `get_settings()` caches one settings object per process; `create_app()` loads it when no settings object is passed.

Use the checked-in [.env.example](../.env.example) as a template. It intentionally leaves required API keys/model and JWT secret blank. Do not put real credentials in documentation or commit a populated `.env` file.

## Application settings

Names below are the exact uppercase environment names accepted by Pydantic Settings. “Required” means there is no application default. Conditional requirements are checked when the image-store adapter is built.

| Variable | Purpose / consumer | Required? and default | Validation | Sensitive? |
|---|---|---|---|---|
| `VISION_SERVICE_URL` | Base URL for Vision HTTP calls (`/detect`, `/reload-model`) | Required | Must be an HTTP(S) URL | No |
| `GEMINI_API_KEY` | Gemini client authentication | Required | Must not be blank; held as `SecretStr` | **Yes** |
| `GEMINI_MODEL` | Model name passed to Gemini | Required | Must not be blank | No |
| `IMAGE_STORE` | Select `memory` or `s3` image adapter | Required | Enum accepts `memory` or `s3` | No |
| `DATABASE_URL` | Async PostgreSQL connection for repositories and Alembic | Required | Must begin `postgresql+asyncpg://`, parse as a URL, and include a database name; held as `SecretStr` | **Yes** (contains credentials) |
| `JWT_SECRET` | HS256 access-token signing secret | Required | At least 32 characters; held as `SecretStr` | **Yes** |
| `S3_BUCKET` | Bucket name when `IMAGE_STORE=s3` | Required when `IMAGE_STORE=s3` | Container raises `ConfigurationError` if absent | No |
| `S3_REGION` | AWS region passed to boto3 when `IMAGE_STORE=s3` | Required when `IMAGE_STORE=s3` | Container raises `ConfigurationError` if absent | No |
| `S3_ENDPOINT_URL` | Optional custom S3-compatible endpoint, e.g. MinIO | Optional; no default (`None`) | Must be an HTTP(S) URL if set | No |
| `CORS_ALLOWED_ORIGINS` | Browser origins allowed by CORS | Optional; empty list (CORS middleware disabled) | Comma-separated; wildcard `*` is rejected | No |
| `MAX_IMAGE_BYTES` | Per-image byte ceiling; also sets request-body limit plus 64 KiB | Optional; `10485760` | Integer greater than 0 | No |
| `MAX_IMAGE_PIXELS` | Decoded image pixel ceiling | Optional; `50000000` | Integer greater than 0 | No |
| `MIN_IMAGE_SIDE_PX` | Minimum width and height side | Optional; `320` | Integer greater than 0 | No |
| `RETAIN_ORIGINAL_IMAGE` | Whether to store the original after successful inference/advisory | Optional; `true` | Boolean | No |
| `IMAGE_URL_TTL_S` | Lifetime used for response-time image URLs | Optional; `900` seconds | Integer from 1 through 604800 | No |
| `DB_POOL_SIZE` | SQLAlchemy async pool size | Optional; `5` | Integer greater than 0 | No |
| `DB_MAX_OVERFLOW` | SQLAlchemy maximum overflow connections | Optional; `5` | Integer at least 0 | No |
| `ACCESS_TOKEN_TTL_S` | JWT lifetime | Optional; `3600` seconds | Integer from 1 through 86400 | No |
| `MAX_ASSESSMENTS_PER_USER_PER_HOUR` | Per-owner persisted-attempt quota | Optional; `30` | Integer greater than 0; value is provisional | No |
| `MAX_CONCURRENT_ASSESSMENTS` | Concurrent workflow slots per service instance | Optional; `4` | Integer greater than 0; value is per process | No |
| `VISION_TIMEOUT_S` | Vision detect HTTP timeout | Optional; `30.0` seconds | Number greater than 0 | No |
| `VISION_CONNECT_TIMEOUT_S` | Vision HTTP connect timeout | Optional; `3.0` seconds | Number greater than 0 | No |
| `VISION_RELOAD_TIMEOUT_S` | Vision reload HTTP timeout | Optional; `60.0` seconds | Number greater than 0 | No |
| `GEMINI_TIMEOUT_S` | Outer and SDK Gemini generation timeout | Optional; `30.0` seconds | Number greater than 0 | No |
| `GEMINI_TEMPERATURE` | Gemini generation temperature | Optional; `0.2` | Number from 0 through 2 | No |
| `GEMINI_MAX_OUTPUT_TOKENS` | Gemini output token limit | Optional; `8192` | Integer greater than 0 | No |
| `LOG_LEVEL` | Python root logger level | Optional; `INFO` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR` | No |

When `IMAGE_STORE=memory`, S3 settings are unused. The memory adapter loses objects on process restart and returns `memory://` URLs that browsers cannot fetch. For `s3`, the bucket and region are required; boto3 uses its default AWS credential chain. `S3_ENDPOINT_URL` changes the endpoint for S3-compatible services such as MinIO.

The maximum HTTP request body is `MAX_IMAGE_BYTES + 65536` bytes to allow multipart headers and boundaries. The image itself is separately capped at `MAX_IMAGE_BYTES`. `MAX_CONCURRENT_ASSESSMENTS` and the same-owner admission guard are process-local. The admin limits endpoint reports the configured operational values.

## Docker Compose variables

These three variables are required by [`docker-compose.yml`](../docker-compose.yml) to initialize its PostgreSQL container; they are not fields in `Settings`:

| Variable | Used by | Requirement |
|---|---|---|
| `POSTGRES_USER` | PostgreSQL image and Compose-generated `DATABASE_URL` | Compose requires a value |
| `POSTGRES_PASSWORD` | PostgreSQL image and Compose-generated `DATABASE_URL` | Compose requires a value; secret |
| `POSTGRES_DB` | PostgreSQL image and Compose-generated `DATABASE_URL` | Compose requires a value |

Compose reads `.env` for interpolation and passes it to the backend using `env_file`. Its explicit `DATABASE_URL` overrides the value in that file to use the Compose service hostname `db`. It also overrides `VISION_SERVICE_URL` with `http://host.docker.internal:9000`. That address must resolve and reach the separately run Vision service from inside the backend container; Compose does not start Vision.

## Startup validation

Missing required settings or invalid field values cause Pydantic Settings validation to fail while the app factory loads settings. Missing `S3_BUCKET` or `S3_REGION` with `IMAGE_STORE=s3` raises a configuration error while the service bundle is built. During application lifespan startup, the backend probes PostgreSQL and executes simple selects on `users.user_id` and `assessments.assessment_id`; it fails if those queries cannot run. This is not an Alembic revision/head comparison and does not guarantee every schema field matches the latest migration. Vision and Gemini connectivity are not startup probes.

For a migration-only command, `migrations/env.py` reads only `DATABASE_URL` (from environment or `.env`), not all application settings. Run `alembic upgrade head` from `backend/` after configuring that URL. See [database](database.md#migrations-and-startup-check) for the migration behavior.
