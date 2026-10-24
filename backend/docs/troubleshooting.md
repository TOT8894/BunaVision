# Troubleshooting

## Contents

- [Settings rejected at startup](#settings-rejected-at-startup)
- [Database connection or schema failure](#database-connection-or-schema-failure)
- [Authentication and authorization responses](#authentication-and-authorization-responses)
- [Invalid or oversized upload](#invalid-or-oversized-upload)
- [Vision timeout or invalid response](#vision-timeout-or-invalid-response)
- [Gemini advisory failure](#gemini-advisory-failure)
- [Image storage or URL failure](#image-storage-or-url-failure)
- [Quota and idempotency responses](#quota-and-idempotency-responses)
- [Asyncio `to_thread` probe times out](#asyncio-to_thread-probe-times-out)

## Settings rejected at startup

**Symptom:** the app factory or service lifespan fails before serving requests with a Pydantic validation/configuration error.

**Likely cause:** one of `VISION_SERVICE_URL`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `IMAGE_STORE`, `DATABASE_URL`, or `JWT_SECRET` is missing or invalid; `JWT_SECRET` is under 32 characters; or `IMAGE_STORE=s3` lacks bucket/region. The app intentionally has no fallback for these required values.

**Safe check:** from `backend/`, load settings without printing values:

```sh
python -c 'from app.core.config import get_settings; get_settings(); print("settings validated")'
```

**Resolution / layer:** fill values in the ignored/local `.env` or deployment secret/environment configuration; ensure `DATABASE_URL` is an async PostgreSQL URL with a database name. This is application configuration.

## Database connection or schema failure

**Symptom:** startup reports that PostgreSQL cannot be reached, or the schema is missing/outdated. `alembic upgrade head` can also fail to connect.

**Likely cause:** PostgreSQL is stopped/unreachable, `DATABASE_URL` points at the wrong host/port/database, credentials are invalid, or the single current migration has not been applied.

**Safe check:**

```sh
pg_isready -h localhost -p 5432
alembic current
```

`alembic current` uses `DATABASE_URL` and contacts the configured database. Do not print the URL into shared logs because it contains credentials.

**Resolution / layer:** start PostgreSQL, correct secret-backed connection settings, then run `alembic upgrade head` from `backend/`. In Docker Compose, the backend URL uses host `db`; from the host, use the published database address. This is a database/infrastructure problem surfaced by application startup.

## Authentication and authorization responses

**Symptom:** `401 AUTHENTICATION_REQUIRED` for protected routes, `401 INVALID_CREDENTIALS` at login, or `403 FORBIDDEN` under `/api/v1/admin`.

**Likely cause:** missing, malformed, expired, wrongly signed, or wrong-issuer bearer token; a user row was removed/deactivated; credentials do not match; or the caller's database role is `user` rather than `admin`.

**Safe check:** obtain a fresh token from `POST /api/v1/auth/login`, then call `/api/v1/auth/me`. A 401 includes `WWW-Authenticate: Bearer`. The API intentionally does not distinguish unknown email from wrong password.

**Resolution / layer:** send `Authorization: Bearer <token>`, sign in again after expiry (default one hour), and have an operator verify the user's role/activity in PostgreSQL for admin access. Admin account creation uses `python -m scripts.create_admin --email ...`; there is no admin-promotion endpoint. There is currently no login brute-force throttle.

## Invalid or oversized upload

**Symptom:** upload returns `400 INVALID_IMAGE`, `413 IMAGE_TOO_LARGE`, `415 UNSUPPORTED_FORMAT`, `422 INVALID_REQUEST`, or `422 IMAGE_NOT_COFFEE`.

**Likely cause:** file bytes are empty, corrupt/truncated, over the byte or pixel ceiling, below the configured minimum side, not decoded as JPEG/PNG/WEBP, request body exceeds image limit plus multipart overhead, or Vision's coffee gate rejects it.

**Safe check:** inspect decoded format and dimensions locally, then compare with `MAX_IMAGE_BYTES`, `MAX_IMAGE_PIXELS`, and `MIN_IMAGE_SIDE_PX`. Avoid uploading a sample containing private data to external diagnostic services. For `IMAGE_NOT_COFFEE`, read the safe `error.details` values.

**Resolution / layer:** upload a readable JPEG/PNG/WEBP that meets configured limits and clearly shows the intended sample; adjust limits only through reviewed configuration if appropriate. The content checks are application-level; a proxy or Vision service may impose additional limits.

## Vision timeout or invalid response

**Symptom:** assessment returns `504 INFERENCE_TIMEOUT` or `502 INFERENCE_FAILED`; admin model reload returns `502 MODEL_RELOAD_FAILED`.

**Likely cause:** Vision is unreachable/slow, its HTTP status is unexpected, its JSON does not match the backend's required fields, a label is unknown, or the returned annotation is not base64 JPEG. The backend calls the configured `VISION_SERVICE_URL` path and does not retry or substitute mock results.

**Safe check:** verify network reachability and the service's own logs. A basic health request can check the Vision process if that deployment provides `/health`, but it does not prove contract compatibility:

```sh
curl -i http://localhost:9000/health
```

Run the backend's mocked contract tests with `python -m pytest tests/adapters/test_vision_client.py`. They do not contact the live service. Compare the checked-in Vision response schema with [the backend's required response fields](vision-integration.md#backend-client-contract).

**Resolution / layer:** make the Vision endpoint reachable and reconcile the documented/source-level schema mismatch between the backend and Vision owners. The currently checked-in Vision code does not provide the backend-required coffee-check fields; no live response has been verified here. This is an integration/contract problem, potentially combined with network infrastructure.

## Gemini advisory failure

**Symptom:** assessment returns `502 ADVISORY_FAILED` and may include an assessment ID because Vision completed before advisory generation failed.

**Likely cause:** invalid key/model, provider/API quota or outage, timeout, empty/truncated response, wrong response schema, missing English/Amharic text, or advisory text outside the length/script checks.

**Safe check:** check whether the configured model is available in the provider account and review the request ID plus service logs. Do not print `GEMINI_API_KEY` or send uploaded image bytes to a Gemini troubleshooting prompt; this adapter is designed to send only derived counts/coverage.

**Resolution / layer:** correct the secret/model configuration or provider/network availability. If an assessment ID is returned, admin history can show the recorded failure when persistence succeeded. This is an external dependency/configuration issue.

## Image storage or URL failure

**Symptom:** `503 PERSISTENCE_FAILED`, missing image URLs, S3 access errors in logs, or returned `memory://` URLs that a browser cannot open.

**Likely cause:** `IMAGE_STORE=memory` (ephemeral/test only), missing S3 bucket/region, AWS credentials/role or bucket policy failure, invalid endpoint, or S3 presigning/deletion failure. URL signing occurs before a completed row is committed.

**Safe check:** confirm `IMAGE_STORE`, bucket and region without printing credentials. For AWS, `aws sts get-caller-identity` checks which identity the CLI uses; it does not necessarily prove the backend's runtime identity. Check backend runtime role permissions and bucket reachability through your deployment diagnostics.

**Resolution / layer:** use an S3-compatible store for browser-accessible durable images, configure the backend's default AWS credential chain and required bucket permissions, and keep the bucket private. If image storage or signing fails, the service attempts cleanup; deletion is best-effort. This is usually infrastructure/storage configuration.

## Quota and idempotency responses

**Symptom:** `429 RATE_LIMITED` with `Retry-After`, or `422 IDEMPOTENCY_KEY_REUSED`.

**Likely cause:** hourly quota reached, service instance has no free assessment slots, a no-key request overlaps another same-owner request, or a key was reused with different uploaded bytes.

**Safe check:** inspect the `Retry-After` response header; an admin can review `/api/v1/admin/assessments?owner_id=...` and `/api/v1/admin/overview`. Do not retry a request with changed bytes under the same key.

**Resolution / layer:** wait the supplied interval for quota/busy errors, or retry the exact same bytes with the same key to replay a completed assessment. Failed attempts do not retain a key, so an identical retry runs again. The configured quota is provisional and its enforcement is not atomic across processes; this is service behavior with a known multi-process consistency limit.

## Asyncio `to_thread` probe times out

**Symptom:** `tests/runtime_probe.py to-thread` reports its two-second asyncio timeout and the process remains alive until an outer timeout kills it; the separate `call-soon-threadsafe` case exits normally.

**Confirmed local observation:** this occurred in standalone isolated probes on CPython 3.13.12 and 3.14.8 on Linux x86_64, as well as the existing CPython 3.14.8 virtual environment. No application imports were needed. The `call_soon_threadsafe` case passed. No 3.12 comparison or full application test result was obtained in that investigation.

**Safe check:** use a process-level bound, not only an asyncio timer:

```sh
timeout 5s python tests/runtime_probe.py to-thread
timeout 5s python tests/runtime_probe.py call-soon-threadsafe
```

**Resolution / layer:** compare a clean runtime using the Dockerfile's Python 3.12 base, a stock CPython build, and another host. Record Python/platform/loop and exact outcomes. The evidence does not identify a specific selector or epoll root cause. This is an observed local Python/runtime environment issue; do not infer that an application suite passed or apply an application workaround based only on this probe.
