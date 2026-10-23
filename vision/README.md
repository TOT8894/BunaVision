# BunaVision — Vision Inference Microservice

A standalone computer vision microservice for green coffee bean defect detection, localization, and visual annotation.

Built with FastAPI, ONNX Runtime, and a fine-tuned YOLOv8 Nano model, this service operates strictly on a data-in / data-out contract: image bytes in -> structured defect detections out.

## 1. Overview & Boundaries

- Decoupled: Contains no AWS SDKs, no databases, and no Gemini multimodal dependencies. All storage, grading rules, and user workflows live in backend/.
- Pure ONNX Runtime: Serves inference with CPU-optimized ONNX Runtime (no heavy PyTorch runtime dependencies in production).
- Two-stage inference: A MobileNetV3-Small domain validator checks for coffee images before YOLO defect detection.
- Decision support only: Results are preliminary AI predictions, not official grading.
- Letterbox Preprocessing: Non-square images are padded with neutral gray (114, 114, 114) to preserve bean aspect ratios during inference.
- Class-Aware NMS: Eliminates overlapping duplicate boxes per defect class, ensuring adjacent defects of different types are not suppressed.
- Fail-Loud Startup: Both ONNX models and their configuration files are validated at startup. Missing or incompatible artifacts prevent the service from starting.

## 2. Directory Layout

```text
vision/
├── core/
│   ├── schemas.py                 # Pydantic schemas for detections, health, errors, and reload
│   ├── yolo_detector.py           # Compatibility shim re-exporting core API
│   └── detection/                 # Modular detection pipeline
│       ├── config.py              # Constants, paths, thresholds, model version
│       ├── labels.py              # Defect taxonomy, classes.json loader, exact classification
│       ├── validator.py           # Coffee / non-coffee domain validator
│       ├── preprocessing.py       # EXIF rotation and letterbox padding
│       ├── postprocessing.py      # Class-aware NMS and box rescaling
│       ├── annotator.py           # Resolution-scaled font/stroke drawing & base64 encoding
│       ├── service.py             # YOLODetectorService orchestrator and get_detector()
│       └── engines/
│           ├── base.py            # DetectionEngine Protocol and RawDetection dataclass
│           ├── onnx_engine.py     # Pure ONNX Runtime engine
│           └── factory.py         # Engine loader (validates and loads best.onnx)
├── service/
│   ├── __init__.py
│   └── main.py                    # FastAPI service (/health, /detect, /reload-model)
├── model/
│   ├── best.onnx                  # Production ONNX weights (640x640 input)
│   ├── best_validator.onnx        # Coffee / non-coffee domain classifier
│   ├── best.pt                    # Checkpoint preserved for retraining notebooks
│   ├── classes.json               # Defect class mapping manifest
│   ├── validator_config.json      # Validator labels, threshold, and model version
│   └── README.md
├── tests/
│   ├── __init__.py
│   ├── test_yolo_detector.py      # Core detector and HTTP endpoint tests
│   ├── test_detection_modules.py  # Unit tests for preprocessing, NMS, and engines
│   └── test_validator.py          # Domain validation and startup tests
├── training/
│   ├── train_coffee_validator.ipynb
│   └── train_yolov8_coffee.ipynb  # YOLOv8n fine-tuning notebook
├── evaluation/                    # Benchmarking and golden images
├── Dockerfile                     # Production container definition
├── requirements.txt               # Pinned dependencies
├── pytest.ini                     # Pytest configuration
└── README.md
```

## 3. Supported Defect Categories

The model detects 3 visible defect classes from the Roboflow dataset manifest (`model/classes.json`):

| Class ID | Raw Label | Canonical English Label | ECX Category |
| :---: | :--- | :--- | :--- |
| `0` | `hitam` | Full Black | Primary Defect |
| `1` | `hitam-sebagian` | Partial Black | Secondary Defect |
| `2` | `kulit-kopi-kecil` | Coffee Husk / Parchment | Secondary Defect |

This detector only localizes supported defects; it does not count total or healthy beans (`total_beans = -1`, `healthy_beans = -1`). The backend may estimate total sample beans separately.

## 4. Prerequisites

- Python 3.11+
- Virtual environment recommended

## 5. Installation

1. Navigate to the `vision` directory:
   ```bash
   cd vision
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Verify `vision/model/best.onnx`, `vision/model/best_validator.onnx`, `vision/model/classes.json`, and `vision/model/validator_config.json` are present.
5. The backend is responsible for validating upload size, format, and image content before calling vision.

## 6. Running the Service

The vision service runs on port 9000.

### Option A: From Repository Root
```bash
uvicorn vision.service.main:app --host 0.0.0.0 --port 9000 --reload
```

### Option B: From Inside vision/
```bash
# Windows PowerShell
$env:PYTHONPATH = ".."
uvicorn service.main:app --host 0.0.0.0 --port 9000 --reload

# Linux / macOS
export PYTHONPATH=".."
uvicorn service.main:app --host 0.0.0.0 --port 9000 --reload
```

### Option C: Using Docker
```bash
docker build -t bunavision-vision:latest -f Dockerfile .
docker run -p 9000:9000 bunavision-vision:latest
```

Rebuilding an image does not update an existing container. Recreate the container after rebuilding to run the new image.

## 7. API Endpoints

Interactive docs are available at `http://localhost:9000/docs`.

### GET /health
Returns YOLO health status, active engine (`onnx`), model path, and supported classes. Both the YOLO detector and domain validator must load successfully before the service starts.

Sample response:
```json
{
  "status": "healthy",
  "service": "vision-detector",
  "engine": "onnx",
  "model_loaded": true,
  "model_path": "vision/model/best.onnx",
  "supported_classes": [
    "Full Black",
    "Partial Black",
    "Coffee Husk / Parchment"
  ]
}
```

### POST /detect
Accepts image bytes as a multipart file plus an optional `confidence` query parameter (default: 0.25, range: 0.05-0.95). The backend owns upload size, format, and image-content validation. Vision reads the supplied bytes, runs the coffee-domain validator, then runs YOLO for accepted coffee images. Non-coffee images are rejected with HTTP 400. Blocking inference runs in worker threads.

Sample request:
```bash
curl -X POST "http://localhost:9000/detect?confidence=0.25" \
  -H "accept: application/json" \
  -F "file=@sample_coffee.jpg"
```

A measured success response from `vision/evaluation/30_174.jpg` at `confidence=0.25` is in the [vision contract example](../contracts/vision-api/examples/detection_success.json). The example's annotated-image Base64 is shortened for documentation; the live endpoint returns the complete value. The [zero-detection example](../contracts/vision-api/examples/detection_zero_defects.json) uses the same image at `confidence=0.95`.

`model_version` identifies the YOLO detector; `validator_version` identifies the coffee-domain model. `coffee_confidence` is the validator's model confidence, not a measure of correctness. A zero-detection result is valid for an accepted coffee image; non-coffee images return HTTP 400 with code `IMAGE_NOT_COFFEE`.

### Error Responses

- `400`: Domain rejection (`detail.code` is `IMAGE_NOT_COFFEE`).
- `422`: Invalid request parameters.
- `500`: Inference processing failure, including bytes that cannot be decoded by the core image pipeline.
- `503`: Model unavailable during inference.

### POST /reload-model
Reloads both ONNX models and their configuration as one bundle. Success returns `reloaded`, `engine`, and `model_path`. If either model fails to load, the active pair remains in use and the endpoint returns HTTP 500.

## 8. Running Automated Tests

Run the test suite from the repository root:

```bash
python -m pytest vision/tests/ -v
```

From inside `vision/`, run `python -m pytest tests/ -v`.

The 49 tests cover:
- Exact defect classification and canonical taxonomy mapping
- Class-aware NMS and high-resolution (>4096px) coordinate suppression verification
- Letterbox image padding (neutral gray 114) and bounding box rescaling
- Resolution-scaled visual annotation drawing with contrast background pills
- Strict manifest validation (loud failure on missing or malformed classes.json, zero silent fallback)
- Domain validator acceptance/rejection, output-shape validation, and startup failures
- Safe model-bundle hot-reloading (preserving both active models if either reload fails)
- Lifespan fail-fast integration tests for missing model artifacts
- Golden-image regression testing on real green coffee bean evaluation photos (vision/evaluation/*.jpg)
- HTTP endpoints: /health, /detect (valid inference, domain rejection, and transparent upload forwarding), and /reload-model
