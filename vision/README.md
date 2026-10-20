# BunaVision — Vision Inference Microservice

A standalone, high-performance computer vision microservice dedicated to **green coffee bean defect detection, localization, and visual annotation**.

Built with **FastAPI**, **ONNX Runtime**, and a fine-tuned **YOLOv8 Nano** model, this service acts as an independent compute component in the BunaVision monorepo. It operates strictly on a data-in / data-out contract: **image bytes in $\rightarrow$ structured defect detections out**.

---

## 1. Overview & Service Boundaries

Per the architecture defined in [`AGENTS.md`](../AGENTS.md) and [`vision/AGENTS.md`](./AGENTS.md):
- **Completely Decoupled:** This service contains **no** AWS SDKs (`boto3`), **no** database connections, and **no** Google Gemini multimodal dependencies. All workflow orchestration, cloud storage, and grading logic reside in the `backend/` service.
- **Contract-Driven:** Exposes an HTTP inference API consumed by the backend. The contract specification lives in [`contracts/vision-api/`](../contracts/vision-api/).
- **Fail-Loud Model Loading:** Does **not** simulate or mock detections. If model weights are missing or unreadable, the service fails explicitly rather than serving fabricated results.

---

## 2. Directory Layout

```text
vision/
├── core/                  # Pure Python detection library (framework-agnostic)
│   ├── schemas.py         # Pydantic schemas (BoundingBox, DetectedBean, YOLODetectionResult)
│   └── yolo_detector.py   # ONNX / PyTorch inference engine, NMS, visual annotation
├── service/               # Thin FastAPI HTTP service layer
│   ├── __init__.py
│   └── main.py            # API routes (/health, /detect, /reload-model)
├── model/                 # Model artifacts and class metadata
│   ├── best.onnx          # Production ONNX weights (640x640 input)
│   ├── best.pt            # PyTorch fallback checkpoint
│   ├── classes.json       # Dataset defect class mapping manifest
│   └── README.md
├── tests/                 # Automated unit and regression test suite
│   ├── __init__.py
│   └── test_yolo_detector.py
├── training/              # Training pipelines and notebooks
│   └── train_yolov8_coffee.ipynb
├── evaluation/            # Model benchmark evaluation and golden images
├── Dockerfile             # Production container definition
├── requirements.txt       # Pinned dependencies
├── pytest.ini             # Pytest configuration
└── README.md              # This documentation
```

---

## 3. Supported Defect Categories

The current fine-tuned YOLOv8n model evaluates three visible defect classes based on the Roboflow dataset manifest ([`model/classes.json`](./model/classes.json)):

| Class ID | Raw Label | Canonical English Label | ECX Defect Category |
| :---: | :--- | :--- | :--- |
| `0` | `hitam` | **Full Black** | Primary Defect (Severe penalty) |
| `1` | `hitam-sebagian` | **Partial Black** | Secondary Defect |
| `2` | `kulit-kopi-kecil` | **Coffee Husk / Parchment** | Secondary Defect |

> **Note on Healthy Beans:** The current model is trained strictly on defective beans. Non-defective (healthy) beans are not localized by this detector (`healthy_beans = -1`). Total sample bean count is estimated by the narrative stage in the backend.

---

## 4. Prerequisites

- **Python:** 3.11 or higher
- **C++ Redistributables:** Required by ONNX Runtime on Windows systems (standard on modern OS installations).
- **Virtual Environment:** Dedicated Python virtual environment recommended.

---

## 5. Installation & Initialization

1. Open your terminal and navigate to the `vision` directory:
   ```bash
   # From the cloned repository root:
   git clone https://github.com/worku404/BunaVision.git
   cd BunaVision/vision
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   ```bash
   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the pinned dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Verify that the production weights exist:
   - Ensure [`model/best.onnx`](./model/best.onnx) (or `best.pt`) is present.

---

## 6. How to Run the Service

The service runs on **port 9000** to remain distinct from the backend API (port 8000) and frontend (port 5173).

Because imports use the monorepo package namespace (`vision.core.*`), ensure the module path is resolved:

### Option A: From the Monorepo Root (Recommended)
```bash
# From repository root (e.g., BunaVision/):
uvicorn vision.service.main:app --host 0.0.0.0 --port 9000 --reload
```

### Option B: From Inside the `vision/` Directory
Set `PYTHONPATH` to the parent repository root before launching:

* **Windows PowerShell:**
  ```powershell
  cd vision
  $env:PYTHONPATH = ".."
  uvicorn service.main:app --host 0.0.0.0 --port 9000 --reload
  ```

* **Windows Command Prompt (CMD):**
  ```cmd
  cd vision
  set PYTHONPATH=..
  uvicorn service.main:app --host 0.0.0.0 --port 9000 --reload
  ```

* **Linux / macOS (Bash / Zsh):**
  ```bash
  cd vision
  export PYTHONPATH=".."
  uvicorn service.main:app --host 0.0.0.0 --port 9000 --reload
  ```

### Option C: Using Docker
```bash
docker build -t bunavision-vision:latest -f Dockerfile ..
docker run -p 9000:9000 bunavision-vision:latest
```

---

## 7. API Endpoints & Interactive Documentation

Once running, access the interactive API documentation:
- **Interactive Swagger UI:** [http://localhost:9000/docs](http://localhost:9000/docs)
- **ReDoc:** [http://localhost:9000/redoc](http://localhost:9000/redoc)
- **OpenAPI JSON Contract:** [http://localhost:9000/openapi.json](http://localhost:9000/openapi.json)

### Available Endpoints

#### 1. `GET /health`
Returns the operational health, active inference runtime (`onnx` or `torch`), model path, and supported defect classes.

**Sample Response (`200 OK`):**
```json
{
  "status": "healthy",
  "service": "vision-detector",
  "engine": "onnx",
  "model_loaded": true,
  "model_path": ".../BunaVision/vision/model/best.onnx",
  "supported_classes": [
    "Full Black",
    "Partial Black",
    "Coffee Husk / Parchment"
  ]
}
```

#### 2. `POST /detect`
Accepts a raw image file (`multipart/form-data`) and an optional `confidence` query parameter.

**Request Parameters:**
- `file` (Form-data, required): JPEG, PNG, or WEBP image ($\le 10\text{ MB}$).
- `confidence` (Query param, optional): Minimum detection threshold (default: `0.25`, range: `0.05` to `0.95`).

**cURL Example:**
```bash
curl -X POST "http://localhost:9000/detect?confidence=0.25" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_beans.jpg"
```

**Sample Response (`200 OK`):**
```json
{
  "model_version": "YOLOv8n-Coffee-ONNX-v1",
  "total_beans": 5,
  "healthy_beans": -1,
  "defect_beans": 5,
  "defect_counts": {
    "Full Black": 2,
    "Partial Black": 3
  },
  "detected_beans": [
    {
      "box": {
        "x1": 142.5,
        "y1": 210.0,
        "x2": 198.2,
        "y2": 275.4
      },
      "class_name": "Full Black",
      "confidence": 0.912,
      "category": "Primary Defect"
    }
  ],
  "annotated_image_base64": "/9j/4AAQSkZJRgABAQAAAQABAAD/..."
}
```

#### 3. `POST /reload-model`
Forces a hot-reload of model weights from `vision/model/` without restarting the process.

---

## 8. Running Automated Tests

Run unit tests directly with `pytest`:

```powershell
# From the repository root
pytest vision/tests/ -v

# Or from the vision/ folder (with PYTHONPATH set)
pytest tests/ -v
```

All tests verify Non-Maximum Suppression (NMS) bounding-box suppression and defect category classification.
