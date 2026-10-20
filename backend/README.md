# BunaVision — Backend Service

> **Python · FastAPI · Pydantic · AWS**
>
> The backend is the **central orchestrator** of the BunaVision system. It owns the public API, validates uploads, coordinates the AI pipeline (YOLO + Gemini), applies ECX grading rules, stores results, and serves them to the frontend. It contains **zero computer-vision logic** — detection lives entirely in the separate Vision service.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Layered Design](#layered-design)
3. [Folder Structure](#folder-structure)
4. [API Convention & Endpoints](#api-convention--endpoints)
5. [Request Flow (Full Assessment)](#request-flow-full-assessment)
6. [External Dependencies](#external-dependencies)
7. [Configuration](#configuration)
8. [Development Setup](#development-setup)
9. [Testing](#testing)
10. [Open Decisions & Known Issues](#open-decisions--known-issues)

---

## Architecture Overview

The backend sits at the center of a three-service architecture:

```
                          ┌────────────────────────────────────────────────┐
                          │              BACKEND  :8000                    │
                          │                                                │
  Browser ──► Frontend ──►│  Routes ──► Services ──► Adapters             │
                          │     │           │            │                  │
                          │     │           │            ├──► Vision HTTP   │──► Vision :9000
                          │     │           │            ├──► Gemini API    │──► Google AI
                          │     │           │            ├──► S3 (boto3)    │──► AWS S3
                          │     │           │            └──► Database      │──► DB (TBD)
                          │     │           │                               │
                          │     │           └──► Domain (grading rules)    │
                          │     └──► Schemas (public contract)            │
                          └────────────────────────────────────────────────┘
```

**Key boundary rules** (from root `AGENTS.md`):

- The backend **never** imports code from `vision/` or `frontend/`. Communication is **HTTP only**.
- The backend treats the Vision service as an **untrusted external dependency**: validate its output, handle its errors/timeouts, never let a vision failure look like a successful assessment.
- The backend owns the **Frontend ⇄ Backend** contract (`contracts/backend-api/`).
- The backend consumes the **Backend ⇄ Vision** contract (`contracts/vision-api/`).

---

## Layered Design

The backend follows a strict layered architecture. Each layer has a single job and communicates only with its neighbors:

```
┌─────────────────────────────────────────────────────────────┐
│  ROUTES  (app/api/)                                         │
│  HTTP in / HTTP out. Validation, status codes, error format.│
│  Never touches boto3, httpx, or the database directly.      │
├─────────────────────────────────────────────────────────────┤
│  SCHEMAS  (app/schemas/)                                    │
│  Pydantic request & response models. The public contract.   │
│  These are what the frontend depends on (via OpenAPI).       │
├─────────────────────────────────────────────────────────────┤
│  SERVICES  (app/services/)                                  │
│  Business logic and workflow orchestration.                  │
│  Know nothing about HTTP transport.                         │
├─────────────────────────────────────────────────────────────┤
│  DOMAIN  (app/domain/)                                      │
│  Pure business rules (ECX grading engine).                  │
│  No I/O, no network, fully unit-testable.                   │
├─────────────────────────────────────────────────────────────┤
│  ADAPTERS  (app/adapters/)                                  │
│  Thin wrappers around external systems. Each behind an      │
│  interface for easy testing and swapping.                    │
│  ├── vision_client/  → calls Vision service over HTTP       │
│  ├── gemini/         → calls Google Gemini API              │
│  ├── storage/        → S3 upload/download (boto3)           │
│  └── db/             → database persistence (TBD)           │
├─────────────────────────────────────────────────────────────┤
│  CORE  (app/core/)                                          │
│  Settings, errors, logging, security — cross-cutting.       │
└─────────────────────────────────────────────────────────────┘
```

**Three kinds of models are kept separate** (never leak one through another):

| Model type | Location | Purpose |
|---|---|---|
| **API schemas** | `app/schemas/` | Public contract — what the frontend sees |
| **Domain models** | `app/domain/` | Business rules (ECX grades, defect points) |
| **Persistence records** | `app/adapters/db/` | Database shapes (TBD) |

---

## Folder Structure

```
backend/
├── AGENTS.md                           # Backend-specific development rules
├── Dockerfile                          # Production container image
├── requirements.txt                    # Python dependencies (pinned)
├── pytest.ini                          # Test runner config
│
├── app/
│   ├── __init__.py
│   │
│   ├── api/                            # ── ROUTES LAYER ──
│   │   └── main.py                     #    FastAPI app, all route handlers
│   │
│   ├── schemas/                        # ── SCHEMA LAYER (public contract) ──
│   │   └── __init__.py                 #    All Pydantic request/response models:
│   │                                   #    CoffeeAssessmentResponse, AssessmentSummary,
│   │                                   #    DefectPrediction, GradeAssessment, CuppingNotes,
│   │                                   #    BilingualSummary, HealthCheckResponse, ErrorResponse,
│   │                                   #    DetectionCoverage, YOLODetectionResult
│   │
│   ├── services/                       # ── SERVICE LAYER ──
│   │   └── __init__.py                 #    (assessment workflow orchestration — WIP)
│   │
│   ├── domain/                         # ── DOMAIN LAYER ──
│   │   └── grading_rules.py            #    ECX defect point equivalency engine
│   │                                   #    Grade thresholds: G1–G5 + Ungraded
│   │                                   #    Only 3 of 13 ECX classes currently detected
│   │
│   ├── adapters/                       # ── ADAPTER LAYER ──
│   │   ├── vision_client/              #    HTTP client for Vision service (stub)
│   │   │   └── .gitkeep
│   │   ├── gemini/                     #    Google Gemini multimodal analysis
│   │   │   └── gemini_vision.py        #    analyze_coffee_sample() — cupping notes,
│   │   │                               #    bilingual summary, grade narrative
│   │   ├── storage/                    #    S3 image upload/download (stub)
│   │   │   └── .gitkeep
│   │   └── db/                         #    Database persistence (stub)
│   │       └── .gitkeep
│   │
│   └── core/                           # ── CROSS-CUTTING ──
│       └── config.py                   #    Settings (env-based), GEMINI_API_KEY, PORT, HOST
│
└── tests/
    ├── __init__.py
    ├── test_api_validation.py          # Upload validation tests
    ├── test_grading_rules.py           # ECX grading engine tests
    └── test_health.py                  # Health endpoint tests
```

---

## API Convention & Endpoints

### URL pattern: `/api/v1/...`

All business endpoints live under the **`/api/v1/`** prefix:

```
https://api.bunavision.com/api/v1/assessments
                          ~~~~~~ ~~~~ ~~~~~~~~~~~
                          prefix  ver  resource
```

**Why `/api/v1/`:**
- Industry standard (GitHub, Stripe, Twilio, AWS all use this pattern).
- `/api/` clearly separates API routes from static assets or frontend routes.
- `/v1/` allows non-breaking evolution — a `/v2/` can coexist without disrupting existing clients.

### Current endpoints

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| `GET` | `/` | API root / discovery | Public |
| `GET` | `/health` | Health check (load balancer probe) | Public |
| `POST` | `/api/v1/assessments` | **Full hybrid AI assessment** (YOLO + Gemini) | TBD |
| `POST` | `/api/v1/detect` | Raw YOLO bounding box detection only | TBD |
| `POST` | `/api/v1/reload-model` | Admin: hot-reload YOLO weights | **Admin only** |

### Planned endpoints (not yet implemented)

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/api/v1/assessments` | List past assessments (paginated) |
| `GET` | `/api/v1/assessments/{id}` | Retrieve a single assessment |
| `DELETE` | `/api/v1/assessments/{id}` | Delete an assessment |

### Error format

All errors use a **consistent structured format** (spec Section 12.5):

```json
{
  "error": {
    "code": "INVALID_IMAGE",
    "message": "Uploaded file is not a supported image (received: text/plain). Please upload JPEG, PNG, or WEBP."
  }
}
```

Error codes: `INVALID_IMAGE`, `IMAGE_TOO_LARGE`, `UNSUPPORTED_FORMAT`, `INFERENCE_FAILED`, `INTERNAL_ERROR`.

### Interactive API docs

When the server is running:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Request Flow (Full Assessment)

When a user uploads an image to `POST /api/v1/assessments`:

```
               ┌──────────────────────────────────────────────────────────────────┐
               │                    POST /api/v1/assessments                      │
               │                                                                  │
  1. VALIDATE  │  Read upload → check MIME type, file size (≤10 MB), decode image │
               │                                                                  │
  2. YOLO      │  POST image bytes to Vision service → structured detections      │
               │  (bounding boxes, defect counts, model version, annotated JPEG)  │
               │                                                                  │
  3. GEMINI    │  Send image + YOLO detections to Gemini →                        │
               │  cupping notes, bilingual summary, grade narrative               │
               │                                                                  │
  4. GRADE     │  Apply ECX grading rules to defect counts →                      │
               │  estimated grade (G1–G5), export eligibility                     │
               │                                                                  │
  5. PERSIST   │  Store annotated image (S3), save assessment record (DB)         │
               │                                                                  │
  6. RESPOND   │  Return CoffeeAssessmentResponse (JSON)                          │
               └──────────────────────────────────────────────────────────────────┘
```

**Key integrity rules:**
- **Never fabricate results.** Missing model output = error state, not zero.
- **"Zero detections" ≠ "processing failed."** These are distinct states.
- Every result records `model_version`, `created_at`, and `status`.
- The result is a **preliminary AI prediction**, never an official grade.

---

## External Dependencies

| System | Adapter | Protocol | Purpose |
|--------|---------|----------|---------|
| **Vision service** | `app/adapters/vision_client/` | HTTP POST (multipart) | Defect localization (bounding boxes) |
| **Google Gemini** | `app/adapters/gemini/` | Google GenAI SDK | Cupping notes, bilingual summaries, advisories |
| **AWS S3** | `app/adapters/storage/` | boto3 | Annotated image storage |
| **Database** | `app/adapters/db/` | TBD | Assessment record persistence |

Each adapter is behind a small interface so it can be faked in tests and swapped without touching business logic.

---

## Configuration

All config is read from environment variables through [`app/core/config.py`](app/core/config.py).

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `GEMINI_API_KEY` | `""` | **Yes** | Google Gemini API key |
| `PORT` | `8000` | No | Server port |
| `HOST` | `0.0.0.0` | No | Bind address |
| `VISION_SERVICE_URL` | — | **Yes** (planned) | Vision service base URL (e.g. `http://vision:9000`) |
| `AWS_S3_BUCKET` | — | Planned | S3 bucket for image storage |
| `DATABASE_URL` | — | Planned | Database connection string |

**Rules:**
- Never put credentials in code or the repo.
- Use AWS IAM roles and the default credential chain.
- Fail at startup if required config is missing — no silent defaults.
- The `.env` file is loaded from `backend/app/.env` (gitignored).

---

## Development Setup

### Prerequisites

- Python 3.11+
- A Google Gemini API key

### Quick start

```bash
# 1. Navigate to backend
cd backend

# 2. Create and activate virtual environment
python -m venv env
# Windows:
env\Scripts\activate
# macOS/Linux:
source env/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
echo "GEMINI_API_KEY=your-key-here" > app/.env

# 5. Run the development server
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# 6. Open API docs
# → http://localhost:8000/docs
```

### With Docker

```bash
# From the backend directory
docker build -t bunavision-backend .
docker run -p 8000:8000 --env-file app/.env bunavision-backend
```

### With docker-compose (all three services)

```bash
# From the repo root
docker-compose up
```

---

## Testing

```bash
# From the backend directory, with the virtual environment activated
pytest -v
```

### Test structure

| Test file | What it covers |
|-----------|---------------|
| `test_api_validation.py` | Upload validation (MIME, size, empty file) |
| `test_grading_rules.py` | ECX grading engine (defect points → grades) |
| `test_health.py` | Health check endpoint |

### Testing philosophy (from `AGENTS.md`)

- **Unit-test services** with fake adapters (fake vision client, fake Gemini, fake S3).
- **Test routes** with FastAPI's `TestClient`.
- **Cover critical paths:** upload validation, vision-failure, Gemini-failure, grading rules.

---

## Open Decisions & Known Issues

> Check `docs/ARCHITECTURE.md` and `docs/MIGRATION.md` for the full list.

### Migration status

This codebase was restructured from a monolith `app/` into three services. Migrated files carry a header comment noting imports that still need rewiring:

```python
# ============================================================
# MIGRATED during repo restructure (monolith app/ -> 3 services).
# TODO(owner): ...
# ============================================================
```

### Known TODOs

| Item | Status | Notes |
|------|--------|-------|
| Wire `vision_client/` adapter (HTTP calls to vision service) | 🟡 Stub | Currently `main.py` still imports YOLO directly — must be replaced with `httpx` calls |
| Move `MODEL_NAME` from hardcoded to env var | 🟡 TODO | Currently `"gemini-2.5-flash"` in `config.py` |
| Implement S3 storage adapter | 🔴 Stub | `.gitkeep` only |
| Implement database adapter | 🔴 Stub | `.gitkeep` only, DB choice undecided |
| Authentication / authorization | 🔴 Not started | Undecided approach |
| Restrict CORS to real frontend origin | 🟡 TODO | Currently `allow_origins=["*"]` |
| Protect `/reload-model` route | 🟡 TODO | Currently public — must be admin-only or internal |
| Extract route handlers into an APIRouter | 🟡 TODO | All routes in one `main.py` — split as they grow |

---

## Related docs

- [`AGENTS.md`](AGENTS.md) — Backend-specific development rules
- [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) — System-wide architecture
- [`../docs/MIGRATION.md`](../docs/MIGRATION.md) — Monolith → 3-service migration guide
- [`../contracts/backend-api/`](../contracts/backend-api/) — Backend API contract (OpenAPI + examples)
- [`../contracts/vision-api/`](../contracts/vision-api/) — Vision API contract (consumed by backend)
