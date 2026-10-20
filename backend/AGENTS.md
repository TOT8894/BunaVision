# Backend (Python / FastAPI / AWS)

Also follow the root `AGENTS.md`. This file adds backend-specific guidance.

The backend orchestrates the workflow and owns the public API. It validates uploads, stores images, **calls the vision service over HTTP**, runs Gemini analysis, applies grading rules, normalizes and persists results, and serves them to the frontend. It contains **no computer-vision/detection logic** — that lives in the `vision/` service.

## Architecture

- Keep clear layers: **routes** (`app/api/`, HTTP only) → **services** (`app/services/`, business logic and workflow) → **adapters / repositories** (`app/adapters/`: `vision_client/`, `gemini/`, `storage/` for S3, `db/`). Routes never touch boto3, httpx, or the database directly. Services know nothing about HTTP transport.
- `app/domain/` holds business rules and statuses (e.g. the ECX grading engine). `app/core/` holds settings, errors, logging, security.
- Put every external system (vision service, Gemini, S3, database) behind a small interface and inject it with FastAPI dependencies. This keeps tests simple and keeps open decisions (database, compute, inference hosting) cheap to change.
- Keep three kinds of models separate: **API schemas** (`app/schemas/`, the public contract), **domain models**, and **persistence records**. Do not leak database or AWS shapes through the API.

## The vision dependency

- The backend calls the vision service through `app/adapters/vision_client/`. Treat vision as an **untrusted external dependency**: validate and normalize its output against a schema, handle its errors and timeouts, and never let a vision failure look like a successful assessment.
- The vision detection schema (`YOLODetectionResult` and friends) belongs to the **vision contract** (`contracts/vision-api/`). The backend re-declares the shapes it consumes as its own vision-client models generated from that contract — it does **not** import vision's Python code.

## API contract

- Pydantic request/response models and the generated OpenAPI (`contracts/backend-api/`) are what the frontend depends on. Always declare response models and meaningful status codes.
- Use one consistent error format. Map domain exceptions to HTTP responses in one central place, not with scattered try/except in routes.
- Avoid breaking changes. Version the API and announce changes to the frontend team (see root rules).
- Paginate list endpoints. Store object keys, not URLs. Create short-lived presigned URLs only when needed and authorized.

## Grading & honesty (backend-specific)

- The current model only detects **3 of 13** ECX defect classes. The grading engine must therefore **not present a definitive ECX grade**: either drop the grade from the MVP, or clearly label it as a rough estimate based on 3 classes with the limitations attached. (See `app/domain/grading_rules.py` and `docs/`.)
- Limit Gemini to narrative output (cupping notes, advisory, Amharic text), clearly labelled AI-generated. Do not present Gemini's visual bean guesses as measured counts; measured counts come from vision.
- Never mark an assessment as completed unless valid results exist. Record failures with a status and error code, never as an empty success.

## Uploads and inference

- The client is untrusted. Validate server-side by **actual content** (decode it), size, and dimensions, never by filename or MIME type alone. Enforce limits.
- Image decoding, HTTP calls to vision/Gemini, and boto3 calls are blocking or I/O-bound. Keep them off the event loop so one slow request cannot starve the others. Move to a worker or queue if latency requires it.

## Consistency and reliability

- Workflows that span S3, the vision service, Gemini, and the database can fail midway. Decide the order of operations and what is left behind on failure. No orphaned state that looks like a success; clean up or make it harmless.
- Retries must be safe. Design for idempotency so a retry does not create duplicate assessments.
- Every assessment records model version, timestamps, and status.

## AWS

- Use roles and the default credential chain. Never put credentials in code or the repo. Least-privilege IAM. Private buckets only.
- Read all configuration from the environment through one typed settings module (`app/core/config.py`). Fail at startup if required config is missing. **No silent defaults** (the migrated config hardcodes the Gemini model name — move it to env).
- Prefer the simplest setup that works. Ask before creating anything billable or leaving it running, and mention the cost implications.
- Infrastructure changes must be reproducible (defined in code under `infra/` or documented), not undocumented console clicks.
- Database, compute, and authentication may still be undecided. Check the docs and code first. If undecided, present the trade-offs and ask.

## Admin & security

- The migrated `/reload-model` route must **not** sit next to public endpoints unprotected. Keep it internal-only (vision service, network-restricted) or remove it.
- Configure CORS for the real frontend origins only (the migrated code uses `*`).

## Python quality

- Full type hints. Keep the linter, formatter, and type checker clean. Pin dependency versions.
- Prefer small, pure functions in services. No mutable module-level state. No network calls at import time.
- Use structured logs that carry a request or assessment ID. Never log secrets, image bytes, or personal data. The health endpoint must not leak configuration.
- If authentication exists, enforce ownership checks on every record access, not only on listing.

## Testing

- Unit-test services with fake adapters (fake vision client, fake Gemini, fake S3). Test routes with FastAPI's test client.
- Cover upload validation, the vision-failure path, the Gemini-failure path, and the grading rules.
