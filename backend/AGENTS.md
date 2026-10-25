# AGENTS.md: backend-drf (migrate the FastAPI backend to Django REST Framework)

Place this file at `backend-drf/AGENTS.md`. Also follow the root `AGENTS.md` (product invariants,
"verify, do not guess", "ask before", "done means verified"). This file wins on conflict.

## Task

Create a new folder `backend-drf/` containing a Django + Django REST Framework backend that does
everything the FastAPI `backend/` does, behind the **same HTTP API**, with **far less code**.

The FastAPI version needed ports, adapters, repositories, a DI container, a hand-written password
hasher, a JWT adapter, a settings class, and async plumbing because FastAPI ships none of them.
Django and DRF already provide most of that. **Use the framework's built-in for everything it
covers. Do not recreate the FastAPI architecture in Django.** If you catch yourself writing a
`Protocol`, a repository class, a container, or a custom auth/hash/pagination/permission/admin
mechanism, stop and look up the Django/DRF feature instead.

Budget: the FastAPI backend is about 4,700 non-test lines. Aim for **under 1,500** non-test lines
of Python in `backend-drf/`. Past 2,000 means you are re-implementing the framework: stop, say so,
and ask.

Do not modify `backend/`, `vision/`, or `frontend/`. Do not overwrite
`contracts/backend-api/openapi.json` (see "Contract").

## Read first (the source of truth for behavior)

1. `backend/app/domain/taxonomy.py`, `analysis.py`, `errors.py`, `models.py`
2. `backend/app/services/assessment_service.py`, `image_validation.py`, `ports.py`
3. `backend/app/adapters/vision_client/` (client + models), `adapters/gemini/` (advisor + prompts),
   `adapters/db/postgres/` (tables, serialization), `adapters/storage/`
4. `backend/app/api/routers/`, `error_handlers.py`, `error_status.py`, `mappers.py`, `schemas/`
5. `backend/README.md`, `contracts/backend-api/openapi.json` (if present)

If anything below disagrees with the running FastAPI code, the code wins: follow the code and
list the discrepancy in your report. Never invent endpoints, fields, or error codes.

## What Django/DRF replaces (do NOT recreate these)

| FastAPI piece | Use instead |
|---|---|
| `ports.py` Protocols, `container.py`, dependency injection | Plain modules and functions. Tests patch clients with `unittest.mock`. |
| `domain/models.py` dataclasses, repositories, in-memory repos | Django models and the ORM |
| SQLAlchemy tables, Alembic, `verify_schema` | `models.py`, `makemigrations`, `migrate` |
| `core/config.py` Settings class | One `config/settings.py` reading env vars, failing fast on missing required ones |
| `UserRepository`, `AuthService`, scrypt hasher, `normalize_email`, dummy-hash timing trick | Custom `User(AbstractUser)` with email login; Django's `authenticate`, password validators and hashers (Django already equalizes timing for unknown users) |
| `JwtTokenIssuer`, bearer dependency | `djangorestframework-simplejwt` |
| `require_admin`, `Role`, `scripts/create_admin.py` | `is_staff` + DRF `IsAdminUser` + `createsuperuser` |
| Cursor codec + keyset queries | DRF `CursorPagination` |
| Hourly quota counting, login throttle (missing in FastAPI) | DRF throttling (`ScopedRateThrottle`) |
| Concurrency semaphore | Remove. Cap with gunicorn `workers x threads` |
| `ImageStore` port, S3 store, in-memory store | Django `STORAGES` + `django-storages` (S3) or `InMemoryStorage` (dev) |
| Pydantic schemas, mappers, `error_handlers.py` | DRF serializers and one `EXCEPTION_HANDLER` |
| `export_openapi.py`, hand-maintained contract | `drf-spectacular` |
| Request-size middleware (async ASGI), `asyncio`, `to_thread` | Remove. Use sync views and a small `Content-Length` check (see "Uploads") |
| Hand-built admin endpoints' UI needs | Django admin site for `User` and `Assessment` (list, filter, search, read-only) |

## Target layout

```
backend-drf/
  AGENTS.md  README.md  manage.py  requirements.txt  Dockerfile  .env.example
  config/            settings.py  urls.py  wsgi.py
  apps/
    common/          exceptions.py (AppError + subclasses + exception handler),
                     middleware.py (request id, body-size check), pagination.py
    accounts/        models.py (User), serializers.py, views.py, admin.py, urls.py
    assessments/
      models.py  serializers.py  views.py  admin_views.py  urls.py  admin.py
      services.py        the pipeline, one function
      taxonomy.py        copied unchanged from the FastAPI version (pure, no framework)
      analysis.py        summarize(), limitations (pure; adapt dataclasses to simple types)
      image_validation.py
      clients/           vision.py  advisor.py  (prompts.py with prompt AND response schema)
```

Three apps only. Keep `taxonomy.py` the single source for defect classes, categories, and which
classes the vision model scans.

## Contract: the frontend must not notice the switch

Same paths, methods, JSON field names, status codes, and error codes as FastAPI. Statuses:

| Error code | HTTP | Error code | HTTP |
|---|---|---|---|
| INVALID_IMAGE | 400 | AUTHENTICATION_REQUIRED | 401 |
| UNSUPPORTED_FORMAT | 415 | INVALID_CREDENTIALS | 401 |
| IMAGE_TOO_LARGE | 413 | FORBIDDEN | 403 |
| IMAGE_NOT_COFFEE | 422 | ASSESSMENT_NOT_FOUND | 404 |
| INVALID_REQUEST | 422 | EMAIL_ALREADY_REGISTERED | 409 |
| IDEMPOTENCY_KEY_REUSED | 422 | RATE_LIMITED | 429 |
| INFERENCE_FAILED | 502 | INFERENCE_TIMEOUT | 504 |
| ADVISORY_FAILED | 502 | PERSISTENCE_FAILED | 503 |
| MODEL_RELOAD_FAILED | 502 | INTERNAL_ERROR | 500 |

DRF defaults to 400 for validation errors: map them to **422 INVALID_REQUEST** in the handler.

**Error envelope** (every error, including DRF's own: 401, 403, 404, 429, parse errors, and DB
errors mapped to 503):
`{"error": {"code", "message", "request_id", "assessment_id": null|str, "details": null|object}}`.
401 responses carry `WWW-Authenticate: Bearer`. Responses carry `X-Request-ID` (accept a valid
incoming one, else generate).

**Endpoints** (prefix `/api/v1`, bearer auth `Authorization: Bearer <token>` unless noted):

| Method and path | Who | Notes |
|---|---|---|
| `GET /health` (no prefix) | anyone | `{"status":"ok","version":...}` |
| `POST /auth/register` | anyone | `{email,password}` -> 201 `{user_id,email,role,created_at}`; `role` is `admin` if `is_staff` else `user` |
| `POST /auth/login` | anyone | `{email,password}` -> `{access_token, token_type:"bearer", expires_in_s}`. Access token only, no refresh token. |
| `GET /auth/me` | user | same shape as register's response |
| `POST /assessments` | user | multipart field `image`; optional `Idempotency-Key` header (1-128 chars). 201 created, **200** on idempotent replay |
| `GET /assessments` | user | own history, newest first, `limit` (1-100, default 20), `cursor` -> `{items, next_cursor}` |
| `GET /assessments/{id}` | user | own only; anyone else's id is 404 |
| `GET /admin/assessments` | admin | all users; filters `status`, `error_code`, `owner_id`; paginated |
| `GET /admin/assessments/{id}` | admin | any user's record |
| `GET /admin/model-versions` | admin | `{versions:[{model_version, validator_version, assessments, first_seen, last_seen}]}` over completed assessments |
| `GET /admin/overview?window_hours=24` | admin | `{since, window_hours, outcomes:[{status, error_code, count}]}` (1-720 hours) |
| `GET /admin/limits` | admin | the enforced limits (values from settings) |
| `POST /admin/vision/reload-model` | admin | calls vision `POST /reload-model`; returns `{reloaded, engine}` only (never `model_path`) |

**Assessment response**, discriminated on `status`:
- completed: `assessment_id, status:"completed", created_at, processing_time_ms, result{model_version,
  image_check{is_coffee:true, coffee_confidence, validator_version}, summary{detection_count,
  primary_detection_count, secondary_detection_count, by_class[{defect{key,name,category},
  count, mean_confidence}]}, detections[{defect, confidence, box{x1,y1,x2,y2}}],
  coverage{scanned[], not_scanned[]}, limitations[{code,message}], advisory{generator_model,
  summary{en,am}, recommendations[{en,am}]}, images{original_url, annotated_url, expires_in_s}}`
- failed (only from GET): `assessment_id, status:"failed", created_at, processing_time_ms, error_code`

List items: completed -> `assessment_id, status, created_at, model_version, detection_count,
primary_detection_count, secondary_detection_count`; failed -> `assessment_id, status, created_at,
error_code`. Admin item: `assessment_id, owner_id, status, created_at, processing_time_ms, error_code,
model_version, validator_version, detection_count`.

Pagination: subclass `CursorPagination` (ordering `-created_at`, `-id`, `page_size_query_param="limit"`,
`max_page_size=100`) and render `{"items": [...], "next_cursor": <the cursor value or null>}`.

**Ids**: assessments keep `asmt_<32 hex>`; users use UUID primary keys (API field `user_id`).

Generate the OpenAPI file with drf-spectacular to `contracts/backend-api/openapi.drf.json`
(never overwrite `openapi.json`), diff it against the FastAPI one, and report every difference.
Model completed/failed as a `oneOf` discriminated by `status` (`PolymorphicProxySerializer`).

## Behavior to preserve (the part that is actually ours)

1. **No fabricated results, no fallbacks.** A failed dependency is an error, never "zero
   detections". Zero detections is a valid completed result.
2. **Validation of the upload** (`image_validation.py`): size <= `MAX_IMAGE_BYTES`; format decided by
   decoding with Pillow (JPEG/PNG/WEBP only, never by filename or MIME type); pixels <=
   `MAX_IMAGE_PIXELS` and shorter side >= `MIN_IMAGE_SIDE_PX` checked from the header *before*
   decoding; then a full `load()` (Pillow's `verify()` accepts truncated JPEGs). Never re-encode
   or resize. Do not use DRF `ImageField` for this.
3. **Pipeline** in `services.create_assessment(user, data, idempotency_key)`, in this order:
   idempotency replay check -> validate image -> vision `/detect` -> map labels through the taxonomy
   -> derive counts -> Gemini advisory -> store images -> save the row.
4. **Vision** (sync `httpx.Client`, created lazily, explicit timeouts; no retries): `POST
   {VISION_SERVICE_URL}/detect`, multipart field `file`, neutral filename (never the user's), forward
   `X-Request-ID`. Read only `model_version, validator_version, is_coffee, coffee_confidence,
   detected_beans[{box,class_name,confidence}], annotated_image_base64`; ignore all other fields
   (counts and categories come from our taxonomy, not vision). Required fields missing -> error.
   - 400 with `detail.code == "IMAGE_NOT_COFFEE"` (or a 200 with `is_coffee == false`) ->
     `NOT_COFFEE` client error: 422 `IMAGE_NOT_COFFEE`, `details={is_coffee:false, coffee_confidence,
     threshold?}`. **Not recorded** in history, no Gemini call, nothing stored.
   - timeout -> INFERENCE_TIMEOUT; connection error, 5xx, 429 -> INFERENCE_FAILED; other non-200 or an
     unusable 200 body (bad box order, confidence outside 0..1, annotated image not valid
     base64 JPEG) -> INFERENCE_FAILED.
   - A label not in the taxonomy fails the assessment (INFERENCE_FAILED). Never guess a category.
5. **Counts** are numbers of *detections* (bounding boxes), never beans. There is no grade, no bean
   totals, no healthy-bean count, no defect percentage, no export eligibility, no cupping notes.
   Coverage ("only N of 13 ECX classes are scanned") and the four limitation codes are derived from the
   taxonomy, never hard-coded.
6. **Gemini** (sync SDK call, `GEMINI_MODEL` from env, no default): receives only the facts (counts per
   class, scanned/not-scanned class names), never the image or any user text. Use structured output
   (`response_schema` + `response_mime_type="application/json"`), keep prompt and schema together in
   `prompts.py`, and validate the reply again: non-empty `en` and `am`, `am` contains Ethiopic
   characters, `en` contains Latin letters, 1-4 recommendations, length limits. Any failure ->
   ADVISORY_FAILED. No canned or offline advisory. Verify SDK names against the installed version.
7. **Failure recording**: if vision, taxonomy, Gemini, image storage, or the DB write fails *after*
   the request was accepted, save an `Assessment` with `status="failed"`, `error_code`, and no result
   (the failed row never holds the idempotency key), then re-raise. Bad input, rejected photos, auth
   and quota errors are not recorded.
8. **Images**: written to storage only after every fallible step succeeded; deleted again if the
   row cannot be saved. `annotated.jpg` when vision supplies one; `original.<ext>` only if
   `RETAIN_ORIGINAL_IMAGE`. Keys: `assessments/<id>/...`. Store keys only; build short-lived URLs
   (`IMAGE_URL_TTL_S`) at response time, never persist them.
9. **Idempotency**: `unique(owner, idempotency_key) where idempotency_key is not null`. Same key and
   same image sha256 -> return the stored result (200). Same key, different image ->
   422 IDEMPOTENCY_KEY_REUSED. Catch the `IntegrityError` from a lost race and replay. Store
   `image_sha256` on every row.
10. **Ownership**: every query for ordinary users filters by `owner=request.user`; someone else's
    assessment is a 404, indistinguishable from a missing one.
11. **Stored result** is one JSON document, schema version 1, identical to the FastAPI one
    (`model_version`, `image_check`, `detections` with `defect_key`, `coverage` keys, `advisory`,
    image keys). Do not store the summary: recompute it from the detections when presenting.
12. **Every result records** the vision `model_version` and `validator_version` and the Gemini model.
13. **Never** log secrets, image bytes, or passwords. Health exposes no configuration.

## Data model

- `accounts.User(AbstractUser)`: `username = None`; `email` unique, stored lower-case, is
  `USERNAME_FIELD`; UUID pk; `is_staff` means admin; deactivate with `is_active=False` (never
  delete users who own history: `on_delete=PROTECT`).
- `assessments.Assessment`: `id` CharField pk; `owner` FK(PROTECT); `status` (completed|failed);
  `created_at`; `processing_time_ms`; `image_sha256`; `idempotency_key` null; `error_code` null;
  `model_version` null; `validator_version` null; `result` JSONField null. Constraints: the
  partial unique above; a check constraint that completed rows have result + model/validator
  versions and no error_code, and failed rows have error_code and none of those (use the
  `condition=` argument your Django version supports). Indexes: `(owner, -created_at, -id)`,
  `(status, -created_at)`.

## Settings and environment

One `config/settings.py`, env-driven. Required settings have **no default** and raise
`ImproperlyConfigured` at startup: `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, `VISION_SERVICE_URL`,
`GEMINI_API_KEY`, `GEMINI_MODEL`, `IMAGE_STORE` (`memory` | `s3`); and `S3_BUCKET`, `S3_REGION`
when `s3`. `DEBUG` defaults to false. Optional (keep these names and defaults): `S3_ENDPOINT_URL`,
`CORS_ALLOWED_ORIGINS` (no `*`), `MAX_IMAGE_BYTES` (10 MiB), `MAX_IMAGE_PIXELS` (50,000,000),
`MIN_IMAGE_SIDE_PX` (320), `RETAIN_ORIGINAL_IMAGE` (true), `IMAGE_URL_TTL_S` (900),
`ACCESS_TOKEN_TTL_S` (3600), `MAX_ASSESSMENTS_PER_USER_PER_HOUR` (30), `VISION_TIMEOUT_S` (30),
`VISION_CONNECT_TIMEOUT_S` (3), `VISION_RELOAD_TIMEOUT_S` (60), `GEMINI_TIMEOUT_S` (30),
`GEMINI_TEMPERATURE` (0.2), `GEMINI_MAX_OUTPUT_TOKENS` (8192), `LOG_LEVEL`.

Key settings: `ATOMIC_REQUESTS = False` (never hold a DB transaction while calling vision or
Gemini; wrap only the insert in `transaction.atomic`); DRF `DEFAULT_AUTHENTICATION_CLASSES` =
simplejwt, `DEFAULT_PERMISSION_CLASSES` = `IsAuthenticated`, public views opt out explicitly;
`DEFAULT_THROTTLE_RATES` with scopes `assessments` (the hourly quota, per user), `auth` (10/min per
IP) on login and register; `CACHES` = `DatabaseCache` (run `createcachetable`) or Redis, because
the default per-process cache would make throttling wrong with several workers; set
`NUM_PROXIES` correctly behind a proxy. `STORAGES["default"]` = S3 (`querystring_auth=True`, no
public ACLs, private bucket) or `InMemoryStorage` for `IMAGE_STORE=memory`, which is development
only (URLs not fetchable; say so in the README).

## Uploads

`DATA_UPLOAD_MAX_MEMORY_SIZE` does not cap file uploads. Add a small middleware that rejects a
request whose `Content-Length` exceeds `MAX_IMAGE_BYTES` + 64 KiB with 413 `IMAGE_TOO_LARGE` in the
standard envelope, and check `image.size` in the view. Recommend the same limit at the reverse
proxy in the README.

## Admin

- **Django admin site**: register `User` (list email, is_staff, is_active; no password editing
  beyond Django's defaults) and `Assessment` (read-only; list id, owner, status, error_code,
  model_version, validator_version, created_at, processing_time_ms; filter by status, error_code,
  model_version; search by id and owner email; no add or delete). This is the dashboard for
  "processing failures recorded" and "model versions recorded".
- **Admin API** above for the frontend. Use ORM aggregates (`values(...).annotate(Count, Min, Max)`),
  not loops. All routes use `IsAdminUser`. Log the acting admin id and result of every
  reload-model call.
- Admins are created with `createsuperuser`; there is no HTTP route that grants admin.

## Running it

gunicorn, `gthread` worker class, an explicit `--timeout` above the vision plus Gemini
timeouts (about 120 s). `workers x threads` is the concurrency cap that replaces the FastAPI
semaphore (default 2 x 4 = 8); document it. Slow requests queue at gunicorn instead of being
rejected: that is an accepted difference. Do not add Celery. Dockerfile runs as a non-root user; migrations are a separate
release step (`python manage.py migrate`), never run on container start. Serve admin static
files with `whitenoise` or the proxy.

## Dependencies (ask before adding; justify each in the PR)

`Django` (current stable; check the official release notes), `djangorestframework`,
`djangorestframework-simplejwt`, `drf-spectacular`, `django-cors-headers`, `django-storages[s3]`
(+ `boto3`), `psycopg[binary]`, `dj-database-url`, `httpx`, `google-genai`, `Pillow`, `gunicorn`,
`whitenoise`. Nothing else without asking. Pin versions in `requirements.txt` from a resolved
install; verify every library's API against the installed version, not memory.

## Work order (stop and report at each checkpoint)

1. Skeleton: settings (fail-fast), `common` (exception handler, request id middleware, body-size
   middleware), `User` model, register/login/me, health. **Checkpoint:** `manage.py check`, migrate,
   login works, errors use the envelope.
2. `Assessment` model, `taxonomy.py`, `analysis.py`, `image_validation.py`, vision client,
   advisor, storage, `services.create_assessment`, list/detail views, pagination, throttles.
   **Checkpoint:** one full upload -> report flow against a stub vision server, plus the
   IMAGE_NOT_COFFEE, replay, and failed-then-retry paths.
3. Admin site + admin API + reload-model.
4. drf-spectacular schema, diff against FastAPI's, README (run steps, env table, accepted
   differences).

## Accepted differences from FastAPI (list them in the README)

Throttling counts requests (replays and rejected uploads included) instead of stored attempts; no
"service busy" 429 (requests queue at gunicorn); password hashing is Django's default (PBKDF2)
instead of scrypt; refresh tokens do not exist in either version; login and register are now
throttled; admin screens come from the Django admin site as well as the API.

## Verification (do not say "done" without it)

Run and report real output: `python manage.py check --deploy`, `makemigrations --check --dry-run`,
`migrate` on an empty PostgreSQL, `spectacular --validate`, and `python manage.py test`. Keep the
tests short and focused (about 15-20 `TestCase`s with the vision and Gemini clients patched): the
pipeline success, zero detections, unknown label, not-coffee, vision failure recorded, advisory
failure recorded, replay, key reuse with a different image, owner isolation, quota 429, non-admin
403 on every admin route, admin failure listing, login failure messages identical for unknown
email and wrong password. If you cannot run something, say so; never imply you did.

## Report back

What you built, how each piece was verified (**verified** / **inferred** / **assumed**), the OpenAPI
differences, the accepted differences, the line count of non-test Python, and anything you could
not run. Do not merge, commit, push, or create AWS resources without asking.
