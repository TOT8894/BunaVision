# BunaVision backend

FastAPI orchestrator. It validates uploads, calls the **vision service over HTTP**, asks Gemini
for a bilingual advisory, stores images and records, and serves them. It contains no detection
logic and imports nothing from `vision/` or `frontend/`.

Results are **preliminary AI predictions**. There is no grade, export eligibility, cupping
analysis or bean total: the vision model only localizes 3 of the 13 ECX defect classes, so none
of those can be computed truthfully.

## Layers (dependencies point downward only)

```
app/api/        routes, middleware, error handlers, mappers   HTTP only, no business logic
app/schemas/    public Pydantic models (the frontend contract)
app/services/   assessment workflow, image validation, ports  no HTTP, boto3, httpx or SDKs
app/domain/     taxonomy, analysis rules, entities, errors     pure Python, no I/O
app/adapters/   vision_client, gemini, storage (S3), db        implement the ports
app/core/       settings, logging, clock, ids, security
app/container.py  composition root (the only place that knows concrete classes)
app/main.py       app factory
```

## API

| Method | Path | |
|---|---|---|
| POST | `/api/v1/assessments` | multipart field `file`; optional `Idempotency-Key` header. 201 new, 200 replay |
| GET | `/api/v1/assessments` | `limit` (1-100), opaque `cursor`; newest first |
| GET | `/api/v1/assessments/{id}` | completed or failed, with fresh image URLs |
| GET | `/health` | liveness only |

All errors use `{"error": {code, message, request_id, assessment_id}}`. `/detect` and
`/reload-model` belong to the vision service and no longer exist here.

## Run

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env        # fill in the required values
uvicorn app.main:app_factory --factory --reload --port 8000
```

Tests: `pytest` (or `python -m unittest discover -s tests/unit -t .` with only Pillow installed).
Checks: `ruff check . && mypy`. Contract: `python -m scripts.export_openapi`.

## Behaviour worth knowing

* Bad input is rejected before any work and not recorded. A dependency failure after that is
  recorded as a `failed` assessment (status + error code, never an empty success).
* Zero detections is a valid `completed` result. Vision errors, unknown defect classes and
  category disagreements between the services fail the assessment.
* Images are written only after every step that can fail has succeeded, and deleted again if
  the final save fails.
* The same `Idempotency-Key` with the same image replays the original result; a different image
  is a 409.

## Open decisions

* **Database.** Only an in-memory repository exists (`ASSESSMENT_STORE=memory`). Implement
  `AssessmentRepository` for DynamoDB or PostgreSQL in `app/adapters/db/` and add the enum
  value and one `case` in `container.py`.
* **Authentication.** `get_principal` returns one shared demo user. Everything else is already
  owner-scoped.
* **Image URLs.** `IMAGE_STORE=memory` URLs are not fetchable; use S3 (or MinIO) to see images.
* **Upload field name.** `file`, matching the vision service. The older spec says `image`.
* **Model/ECX facts to confirm.** Minimum image side (320 px) and the 13-class inventory in
  `app/domain/taxonomy.py`.
