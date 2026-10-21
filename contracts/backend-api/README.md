# Backend API Contract (Frontend ⇄ Backend)

**Owner:** Backend members (`@worku404`, `@danieltuemay350-web`).  
**Consumer:** Frontend members (`@TOT8894`, `@mikimek23`).

This directory contains the **single source of truth** for the public HTTP API between the frontend browser application and the backend service. The frontend generates its TypeScript types from the `openapi.json` committed here.

---

## 1. Committed Artifacts

* **[`openapi.json`](./openapi.json)**: The official OpenAPI 3.1.0 schema generated directly from FastAPI. It formally defines:
  - `GET /health`: Liveness probe returning `status: "ok"` and `version`.
  - `POST /api/v1/assessments`: Synchronous assessment from uploaded green coffee photo (multipart/form-data). Supports `Idempotency-Key` header.
  - `GET /api/v1/assessments`: Cursor-paginated history of assessments (newest first).
  - `GET /api/v1/assessments/{assessment_id}`: Fetch a single assessment (completed or failed) with fresh signed S3 image URLs.
* **[`examples/`](./examples/)**: Concrete JSON payloads representing realistic responses:
  - `create_assessment_201.json`: Successful completed assessment with defect detections, summary, coverage, limitations, bilingual advisory, and S3 URLs.
  - `error_invalid_image_400.json`: Universal error envelope for client validation failures.
  - `error_inference_failed_502.json`: Universal error envelope for downstream dependency failures.

---

## 2. Endpoints Overview (For Frontend Devs)

### `GET /health`
Liveness probe. Used by load balancers and deployment scripts.
- **200 OK**: `{ "status": "ok", "version": "0.4.0" }`

### `POST /api/v1/assessments`
Uploads a green coffee image for preliminary defect screening.
- **Content-Type**: `multipart/form-data` with field `image` (JPEG, PNG, WEBP; max 15MB).
- **Optional Header**: `Idempotency-Key` (UUID). If reused with the identical image, returns the previously computed result with `200 OK` instead of re-running inference.
- **201 Created**: Returns `CompletedAssessmentOut`.
- **4xx/5xx**: Returns universal `ErrorResponse` envelope.

### `GET /api/v1/assessments`
Retrieves past assessments for the authenticated user, newest first.
- **Query params**:
  - `limit` (integer, default 20, max 100)
  - `cursor` (opaque string from `next_cursor` of previous page)
- **200 OK**: Returns `AssessmentListOut` with `items` and `next_cursor`.

### `GET /api/v1/assessments/{assessment_id}`
Retrieves a specific assessment by ID.
- **200 OK**: Returns `AssessmentOut` (discriminated union on `status: "completed" | "failed"`). Presigned S3 image URLs are refreshed with a fresh 15-minute expiry (`expires_in_s: 900`).

---

## 3. How to Generate `openapi.json`

Whenever schemas or routers in `backend/app/` are modified, regenerate `openapi.json`:

From the `backend/` directory (with your virtual environment active):
```powershell
python -m scripts.export_openapi
```

---

## 4. Frontend Type Generation

The frontend team generates TypeScript interfaces directly from this schema:

```bash
npx openapi-typescript contracts/backend-api/openapi.json -o frontend/src/api/types.d.ts
```

Per [AGENTS.md](../../AGENTS.md), contract changes affect both frontend and backend and require review from both owners before merging.
