# BunaVision backend

Python, FastAPI, PostgreSQL. It owns the public API: sign-in, photo upload, history, and the
administrator tools. It never imports vision code: detection happens in the vision service,
reached over HTTP only. It contains no computer-vision logic.

Results are preliminary AI predictions, never official grades.

## Layout

```
app/
  api/        HTTP only: routers, dependencies, error mapping, middleware, mappers
  schemas/    public API models (the contract the frontend generates types from)
  services/   workflows: assessments, auth, admin; ports.py lists everything they need
  domain/     pure rules and vocabulary: taxonomy, models, errors, users, operations
  adapters/   implementations of the ports
    vision_client/  HTTP client for the vision service (detect + reload-model)
    gemini/         advisory writer (structured output; prompts.py holds prompt and schema)
    storage/        S3 and in-memory image stores
    db/             PostgreSQL repositories (+ in-memory ones for tests)
    security/       scrypt password hashing, JWT tokens
  core/       settings, logging, clock, ids
  container.py   the one place that wires ports to adapters
migrations/   Alembic (async)
scripts/      create_admin.py, export_openapi.py
```

Dependencies point inward: `api -> services -> domain`, and `adapters -> services.ports`.

## Run it

```bash
cp .env.example .env            # then fill in the required values
docker run -d --name bunavision-db -e POSTGRES_USER=bunavision \
  -e POSTGRES_PASSWORD=change-me -e POSTGRES_DB=bunavision -p 5432:5432 postgres:16
pip install -r requirements.txt
alembic upgrade head                                   # create the tables
python -m scripts.create_admin --email you@example.com  # prompts for a password
uvicorn app.main:create_app --factory --port 8000
```

The app refuses to start (with a message saying what to do) if a required setting is missing,
the database is unreachable, or migrations have not been applied. Docs: `/docs`.

## Endpoints (`/api/v1`)

| Method and path | Who | Purpose |
|---|---|---|
| `POST /auth/register` | anyone | create an account (role `user`) |
| `POST /auth/login` | anyone | email + password -> bearer token |
| `GET /auth/me` | signed in | the current user |
| `POST /assessments` | signed in | upload a photo (multipart field `image`); optional `Idempotency-Key` header |
| `GET /assessments` | signed in | your history, newest first, cursor-paginated (`limit`, `cursor`) |
| `GET /assessments/{id}` | signed in | one of your assessments |
| `GET /admin/assessments` | admin | every user's attempts; filter `status`, `error_code`, `owner_id` |
| `GET /admin/assessments/{id}` | admin | one attempt from any user |
| `GET /admin/model-versions` | admin | vision model + validator versions that produced results |
| `GET /admin/overview?window_hours=24` | admin | outcome counts: completed, failed by error code |
| `GET /admin/limits` | admin | the upload, quota and timeout limits being enforced |
| `POST /admin/vision/reload-model` | admin | ask the vision service to reload its model |
| `GET /health` | anyone | liveness |

Admin duties map to the spec's section 5.3 stories: failures recorded (`/admin/assessments`,
`/admin/overview`), model versions recorded (`/admin/model-versions`), limits (`/admin/limits`,
enforced by the request-size middleware, image validation, the per-user hourly quota, and the
concurrent-assessment cap).

An admin cannot be created over HTTP. Use `scripts/create_admin.py`.

## Photos that are not coffee

The vision service gates every photo. If it decides the photo is not green coffee beans, the
backend answers `422` with `error.code = "IMAGE_NOT_COFFEE"` and
`error.details = { is_coffee: false, coffee_confidence, threshold }`. That is not a processing
failure: nothing is stored, nothing counts against failure statistics, and Gemini is not
called. A completed assessment carries `result.image_check` (`is_coffee: true`, confidence and
validator version).

## Rules the code keeps

- No fallbacks or fabricated results. A failed dependency is an error, never "zero detections".
  Zero detections is a valid completed result.
- Failures after the request was accepted are recorded (status `failed` + error code), so admins
  can see them. Bad input and rejected photos are not recorded.
- Counts are numbers of detections (bounding boxes), never bean counts. The old bean totals,
  healthy-bean count, defect percentage, grade, export eligibility and cupping notes are gone:
  the vision model cannot support them.
- Class coverage ("only 3 of 13 ECX classes are scanned") is derived from `domain/taxonomy.py`.
  An unknown vision label fails the assessment instead of being guessed.
- Gemini only ever sees the detector's counts, never the image or user text.
- Every result stores the vision model version and coffee-validator version.

## Open items

- Login has no brute-force throttle yet (scrypt cost is the only friction). Add per-IP/email
  limits before exposing it publicly.
- No refresh tokens: access tokens last `ACCESS_TOKEN_TTL_S` (default 1 hour), then log in again.
- `IMAGE_STORE=memory` is development only. Use `s3` (or MinIO via `S3_ENDPOINT_URL`) to show
  images in the frontend.
- Quotas and the concurrency cap are provisional numbers: choose them from real usage.
- `requirements.txt` has version ranges; lock it (`pip-compile`) before building images.
