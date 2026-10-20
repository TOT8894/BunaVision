# Vision API contract (Backend ⇄ Vision)

**Owner:** Vision member. **Consumer:** Backend members.

This is the single source of truth for the HTTP inference API between the backend and the vision service. The backend generates its vision-client models from the `openapi.json` here — it does **not** import vision's Python code.

## What goes here

- `openapi.json` — the OpenAPI document for the vision inference API (image bytes in → structured detections out, including model version).
- `examples/` — example detection responses so the backend can build and mock before the vision service is live.

## The contract must document

- The output schema (currently `BoundingBox`, `DetectedBean`, `YOLODetectionResult` — see `vision/core/schemas.py`).
- Class names and the fixed class/label map (currently 3 classes: Full Black, Partial Black, Coffee Husk / Parchment).
- Confidence range, coordinate format and units (pixel vs normalized, box convention), and exactly what is counted.
- The model version field.

## Rules

- On day one, commit a stub endpoint + example JSON so the backend can start in parallel.
- Any change here affects the backend. Propose it first, update this contract in the **same change** as the vision code, and get review from both sides (see `/.github/CODEOWNERS`).

> TODO(vision owner): generate and commit `openapi.json` + examples from the thin service in `vision/service/`.
