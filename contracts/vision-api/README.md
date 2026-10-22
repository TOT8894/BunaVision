# Vision API Contract (Backend ⇄ Vision)

**Owner:** Vision member (`@josi1219`).  
**Consumer:** Backend members (`@worku404`, `@danieltuemay350-web`).

This directory contains the **single source of truth** for the HTTP inference API between the backend and the vision service. The backend uses the schemas and examples here to implement its vision client (`backend/app/adapters/vision_client/`) without importing code from `vision/`.

---

## 1. Committed Artifacts

* **[`openapi.json`](./openapi.json)**: The official OpenAPI 3.1.0 schema generated directly from [`vision/service/main.py`](../../vision/service/main.py). It formally defines:
  - `POST /detect`: Accepts multipart/form-data images, returns `YOLODetectionResult`.
  - `GET /health`: Health check, engine type, and model status.
  - `POST /reload-model`: Administrative model reload endpoint.
* **[`examples/detection_success.json`](./examples/detection_success.json)**: Concrete JSON payload returned when defects are detected (localized boxes, counts, both model versions, domain-validation confidence, and annotated bare Base64 JPEG preview).
* **[`examples/detection_zero_defects.json`](./examples/detection_zero_defects.json)**: JSON payload returned for an accepted coffee image with zero defect detections.

---

## 2. How to Re-generate `openapi.json`

Whenever endpoints or schemas in `vision/` are modified, update `openapi.json` using one of two methods:

### Option 1 (Via Browser)
1. Start the vision service:
   ```bash
   uvicorn vision.service.main:app --port 9000
   ```
2. Open [http://localhost:9000/openapi.json](http://localhost:9000/openapi.json) in your browser.
3. Save the response directly into `contracts/vision-api/openapi.json`.

### Option 2 (One-Line CLI Command)
From the repository root:

* **Windows PowerShell:**
  ```powershell
  python -c "import json; from vision.service.main import app; print(json.dumps(app.openapi(), indent=2))" | Out-File -Encoding utf8 contracts/vision-api/openapi.json
  ```

* **Linux / macOS (Bash):**
  ```bash
  python3 -c "import json; from vision.service.main import app; print(json.dumps(app.openapi(), indent=2))" > contracts/vision-api/openapi.json
  ```

---

## 3. Schema & Labeling Rules

Per [vision/AGENTS.md](../../vision/AGENTS.md):
- **Model Version:** Every response must include `model_version: "YOLOv8n-Coffee-ONNX-v1"`.
- **Validator Version:** Every successful detection response includes `validator_version`, identifying the active coffee-domain model.
- **Supported Defect Classes:** Currently 3 classes:
  - `Full Black` (Primary Defect)
  - `Partial Black` (Secondary Defect)
  - `Coffee Husk / Parchment` (Secondary Defect)
- **Healthy Beans:** YOLO does not localize healthy beans (`healthy_beans = -1`). Total sample count is estimated by Gemini in the backend.
- **Contract Changes:** Any change to this directory affects the backend. Propose it first, update this contract in the same pull request as the vision code, and request review from `@worku404` or `@danieltuemay350-web`.
