# Backend API contract (Frontend ⇄ Backend)

**Owner:** Backend members. **Consumer:** Frontend members.

This is the single source of truth for the public HTTP API between the browser app and the backend. The frontend generates its TypeScript types from the `openapi.json` here — nobody hand-copies shapes.

## What goes here

- `openapi.json` — the OpenAPI document for the backend's public API. The backend generates it from its FastAPI/Pydantic models (`backend/app/schemas/`) and commits it here.
- `examples/` — example request/response JSON so the frontend can build and mock before the backend is live.

## Rules

- On day one, commit stub endpoints + example JSON so the frontend can start in parallel.
- Any change here affects the frontend. Propose it first, update this contract in the **same change** as the backend code, and get review from both sides (see `/.github/CODEOWNERS`).
- CI should fail if the committed `openapi.json` no longer matches the backend code.

> TODO(backend owner): generate and commit `openapi.json` + examples. The public response shapes currently live in `backend/app/schemas/__init__.py` (migrated from the old `app/schemas.py`).
