# BunaVision backend (Django REST Framework)

The same HTTP API as the FastAPI `backend/`, built with Django and DRF so the framework supplies
what the FastAPI version hand-wrote: users and password hashing, JWT auth, cursor pagination,
throttling, the ORM and migrations, storage backends, the admin site and the OpenAPI schema.
Results are preliminary AI predictions, never official grades.

## Run it

```bash
cp .env.example .env && $EDITOR .env && set -a && source .env && set +a
docker run -d --name bunavision-db -e POSTGRES_USER=bunavision -e POSTGRES_PASSWORD=change-me \
  -e POSTGRES_DB=bunavision -p 5432:5432 postgres:16
pip install -r requirements.txt
python manage.py migrate
python manage.py createcachetable                      # shared throttle counters (skip with REDIS_URL)
python manage.py createsuperuser                       # an administrator (email + password)
gunicorn config.wsgi:application --worker-class gthread --workers 2 --threads 4 --timeout 120
```

Initial migrations are included. Apply them as a separate release step with `python manage.py
migrate`; do not run migrations on container startup. Docs: `/api/docs/`, schema: `/api/schema/`,
dashboard: `/django-admin/`.

## Tests

```bash
python -m unittest apps.assessments.tests.test_pure       # framework-free, no setup
SECRET_KEY=t ALLOWED_HOSTS=localhost DATABASE_URL=sqlite:///test.sqlite3 VISION_SERVICE_URL=http://vision.test \
  GEMINI_API_KEY=x GEMINI_MODEL=x IMAGE_STORE=memory python manage.py test
```

## Layout

```
config/            settings.py (env-driven, fails fast), urls.py, wsgi.py
apps/common/       errors (pure), handler (DRF -> error envelope), middleware, pagination
apps/accounts/     User (email login), register / login / me, admin
apps/assessments/  Assessment model, services.py (the pipeline), clients/ (vision, Gemini),
                   taxonomy / analysis / image_validation (pure), views, admin_views, admin
```

## API (`/api/v1`) and who can call it

| Method and path | Who |
|---|---|
| `POST /auth/register`, `POST /auth/login` | anyone (throttled per IP) |
| `GET /auth/me` | signed in |
| `POST /assessments` (multipart `image`, optional `Idempotency-Key`), `GET /assessments`, `GET /assessments/{id}` | signed in; hourly quota per user |
| `GET /admin/assessments` (filters `status`, `error_code`, `owner_id`), `GET /admin/assessments/{id}`, `GET /admin/model-versions`, `GET /admin/overview`, `GET /admin/limits`, `POST /admin/vision/reload-model` | `is_staff` only |
| `GET /health` (no prefix) | anyone |

A photo that is not green coffee gets `422 IMAGE_NOT_COFFEE` with
`error.details = {is_coffee: false, coffee_confidence, threshold}`; it is not stored or counted as a
failure and Gemini is not called. Failures after a request was accepted (vision, unknown label,
Gemini, storage, database) are recorded as failed assessments and shown in the admin site.

## Differences from the FastAPI backend

- The quota counts requests (replays and rejected uploads included), not stored attempts.
- There is no "service busy" 429: requests queue at gunicorn. `workers x threads` is the cap.
- Passwords use Django's default hasher (PBKDF2), not scrypt.
- `limit` outside 1-100 is clamped by DRF, not rejected with 422.
- Login and register are throttled (10/min per IP); the FastAPI version had no throttle.
- Admin screens come from the Django admin site as well as the API.
- Unchanged: no refresh tokens, `IMAGE_STORE=memory` is development only.

## Open items

- Pin `requirements.txt` (`pip-compile`) and confirm the DRF, simplejwt and drf-spectacular versions
  support the Django you install.
- Put the same upload size limit at the reverse proxy (`client_max_body_size`); set `NUM_PROXIES`.
- Run `python manage.py check --deploy` and `spectacular --validate` and compare the schema with
  `contracts/backend-api/openapi.json` before pointing the frontend here.
