# Vision API Contract (Backend ⇄ Vision)

**Owner:** Vision member (`@josi1219`).  
**Consumer:** Backend members (`@worku404`, `@danieltuemay350-web`).

This directory contains the **single source of truth** for the HTTP inference API between the backend and the vision service. The backend uses the schemas and examples here to implement its vision client (`backend/app/adapters/vision_client/`) without importing code from `vision/`.

---

## 1. Committed Artifacts

* **[`openapi.json`](./openapi.json)**: The official OpenAPI 3.1.0 schema generated directly from [`vision/service/main.py`](../../vision/service/main.py). It formally defines:
  - `POST /detect`: Accepts multipart/form-data image bytes and documents success, domain-rejection, request-shape, and inference-error responses.
  - `GET /health`: Health check, engine type, and model status.
  - `POST /reload-model`: Administrative model reload endpoint with typed success and failure responses.
* **[`examples/detection_success.json`](./examples/detection_success.json)**: Measured response for `vision/evaluation/30_174.jpg` at confidence threshold `0.25` (five detections). The annotation Base64 is shortened for documentation and is not decodable.
* **[`examples/detection_zero_defects.json`](./examples/detection_zero_defects.json)**: Measured response for the same accepted coffee image at confidence threshold `0.95`, which produces zero defect detections.

The backend validates upload size, format, and image content before calling vision. The vision service does not implement duplicate upload-policy checks; it receives the bytes and runs domain validation and inference.

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
- **Model Versions:** Every successful `/detect` response includes `model_version` for YOLO and `validator_version` for the coffee-domain model.
- **Confidence:** `confidence` in each detection and `coffee_confidence` are model confidence scores, not measures of correctness.
- **Bounding Boxes:** `x1`, `y1`, `x2`, and `y2` are pixel coordinates in the original image; the first pair is the top-left and the second pair is the bottom-right.
- **Counts:** `total_beans = -1` means YOLO does not estimate total sample beans. `defect_beans` counts localized defect instances, and `defect_counts` breaks them down by class. `healthy_beans = -1` means healthy beans are not counted.
- **Upload Validation:** The backend owns upload size, format, and image-content validation. The vision service may return HTTP 500 if invalid bytes reach the inference core.
- **Supported Defect Classes:** Currently 3 classes:
  - `Full Black` (Primary Defect)
  - `Partial Black` (Secondary Defect)
  - `Coffee Husk / Parchment` (Secondary Defect)
- **Healthy Beans:** YOLO does not localize healthy beans (`healthy_beans = -1`). Total sample count is estimated by the backend.
- **Contract Changes:** Any change to this directory affects the backend. Propose it first, update this contract in the same pull request as the vision code, and request review from `@worku404` or `@danieltuemay350-web`.
