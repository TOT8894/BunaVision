# MIGRATION.md — monolith → three services

This repo was restructured from a single `app/` FastAPI monolith into a **three-service monorepo** (`frontend/`, `backend/`, `vision/`) plus shared `contracts/`, `infra/`, and `docs/`.

**What was done:** folders, build config, docs, AGENTS.md, and the **physical move of existing code** into its new home. **No application logic was rewritten.** Moved Python files carry a header comment flagging imports that still point at the old `app.*` layout. Each service's own member finishes the wiring.

---

## File moves (code is unchanged)

| Old location | New location | Notes |
|---|---|---|
| `app/services/yolo_detector.py` | `vision/core/yolo_detector.py` | imports `app.schemas` → `vision.core.schemas` |
| `app/schemas.py` (vision classes) | `vision/core/schemas.py` | `BoundingBox`, `DetectedBean`, `YOLODetectionResult` |
| `app/schemas.py` (API classes) | `backend/app/schemas/__init__.py` | summary, predictions, grade, cupping, bilingual, response, health, error |
| `models/*` | `vision/model/` | `best.onnx`, `best.pt`, `classes.json`, `README.md` |
| `notebooks/train_yolov8_coffee.ipynb` | `vision/training/` | |
| `app/services/gemini_vision.py` | `backend/app/adapters/gemini/gemini_vision.py` | |
| `app/services/grading_rules.py` | `backend/app/domain/grading_rules.py` | self-contained |
| `app/main.py` | `backend/app/api/main.py` | routes split — see below |
| `app/config.py` | `backend/app/core/config.py` | |
| `tests/test_yolo_detector.py` | `vision/tests/` | |
| `tests/test_{health,api_validation,grading_rules}.py` | `backend/tests/` | |
| root `Dockerfile` / `requirements.txt` / `pytest.ini` | per-service copies in `backend/` and `vision/` | root copies deleted |

Old `app/`, `models/`, `notebooks/`, `tests/` directories were removed.

## Route split (from the old `app/main.py`)

| Route | Goes to |
|---|---|
| `POST /detect`, `GET /health`, `POST /reload-model` | **vision** service (`vision/service/`), internal only |
| `POST /assessments` | **backend** (`backend/app/api/` + `backend/app/services/`) |

---

## What each member still needs to implement

Nothing below was written for you — these are the wiring/finishing tasks the restructure intentionally left to the owners.

### Vision (1 member) — `vision/`
- [x] Rewire `core/yolo_detector.py` import and extract modular detection architecture into `vision/core/detection/`.
- [x] Build the thin `vision/service/` FastAPI wrapper over `core/` (`/detect`, `/health`, and `/reload-model`). Zero detection logic in the service layer.
- [x] **Remove the silent mock fallback** (`_fallback_demo` completely eliminated; fail-fast enforced in core engines and FastAPI lifespan).
- [x] Establish pure ONNX Runtime serving path (`best.onnx`); retain `best.pt` exclusively for retraining in Colab/notebooks.
- [x] Publish `contracts/vision-api/openapi.json` + examples (synchronized OpenAPI 3.1.0 schema with typed HealthResponse and bare Base64).
- [x] Add dynamic `model_version` and class manifest validation to every response.

### Backend (2 members) — `backend/` + `infra/`
- [ ] Rewire imports in `app/api/main.py`, `app/adapters/gemini/gemini_vision.py`, `app/core/config.py` away from the old `app.*` monolith paths.
- [ ] Implement `app/adapters/vision_client/` — call the vision service over HTTP (httpx) instead of importing `yolo_detector`. Validate/normalize its output; handle timeouts and errors.
- [ ] Generate the backend vision-client models from `contracts/vision-api/`.
- [ ] Keep only `/assessments` (+ a backend `/health`) in the backend; `/detect` and `/reload-model` belong to vision. Make any admin route internal-only (the migrated `/reload-model` was public).
- [ ] Move the Gemini model name out of the hardcoded `config.py` into env (`GEMINI_MODEL`). Fail at startup if required config is missing; no silent defaults.
- [ ] Fix CORS: the migrated code uses `*` — restrict to the real frontend origins.
- [ ] **Grading honesty:** the model detects only 3 of 13 ECX classes, so `domain/grading_rules.py` must not present a definitive grade — drop it from the MVP or clearly label it a rough 3-class estimate.
- [ ] Implement `app/adapters/storage/` (S3; add `boto3` to requirements) and `app/adapters/db/` (database TBD).
- [ ] Publish `contracts/backend-api/openapi.json` + examples from the Pydantic models.
- [ ] `infra/` — AWS as code (compute + DB choices still open).

### Frontend (2 members) — `frontend/`
- [ ] Initialize the React/TypeScript/Tailwind app (toolchain of your choice, e.g. Vite) — `frontend/package.json` is a placeholder.
- [ ] Generate TypeScript types from `contracts/backend-api/openapi.json`.
- [ ] Build `src/api/` (the one place that calls the network), `src/features/` (home, upload, assessment, history, auth), `src/components/`, `src/strings/` (EN/AM), `src/mocks/` (contract-shaped, clearly marked).
- [ ] Model all UI states explicitly; keep "no defects" and "analysis failed" visually distinct; never show a definitive grade.

### Shared / everyone
- [ ] Replace placeholder handles in `/.github/CODEOWNERS` with real GitHub usernames.
- [ ] Fill in `docker-compose.yml` service entry points once each service runs.
- [ ] `API_INTEGRATION_GUIDE.md` is superseded by the generated OpenAPI in `contracts/` — keep it only as a human overview or delete it.

---

## Not yet implemented at all (flagged, not created)

These were never in the monolith and were **not** scaffolded with logic — only empty placeholders exist:
- S3 storage adapter and the database layer (`backend/app/adapters/storage`, `.../db`).
- Authentication / user accounts (spec leaves this undecided).
- The entire frontend application (only `package.json` + empty `src/` folders exist).
- The vision HTTP service wrapper (`vision/service/` is fully implemented and tested).
- Backend OpenAPI contract document (`contracts/backend-api/openapi.json`; `contracts/vision-api/` is published and tested).
- `infra/` AWS definitions.
