# BunaVision — Vision Module: Project State

> **For agents:** This file is a temporary living document. Update it when you complete a task or
> make a significant decision. It is **not** an architecture spec — read `AGENTS.md` for invariants
> and constraints. Read this file to understand where things stand *right now* and what is next.

---

## Status at a Glance

| Item | State |
|:-----|:------|
| Core ONNX detection pipeline | ✅ Complete |
| FastAPI service | ✅ Complete |
| Test suite (47 tests) | ✅ All passing |
| Docker container | ✅ Built and validated (`bunavision-vision:latest`) |
| OpenAPI contract | ✅ Synced (`contracts/vision-api/openapi.json`) |
| Documentation | ✅ Aligned with current architecture |
| Git branch | `vision` — 4 commits ahead of `main` |
| Coffee domain validator | ✅ Complete & verified (MobileNetV3-Small ONNX, 6.09 MB, fail-fast HTTP 400 gate) |

---

## Current Architecture

Two layers, strictly separated:

```
vision/core/          ← pure Python library — all inference logic lives here
vision/service/       ← thin FastAPI skin — no detection logic, only HTTP plumbing
```

### Inference flow (two-stage pipeline)

```
POST /detect (image bytes)
        │
        ▼
  DomainValidator (vision/core/detection/validator.py)
    loads:  vision/model/best_validator.onnx  (MobileNetV3-Small, 6.09 MB)
            vision/model/validator_config.json
        │
        ├── P(coffee) < 0.75 ──► HTTP 400 Bad Request
        │                        {"detail": {"code": "IMAGE_NOT_COFFEE", "confidence": 0.21, "threshold": 0.75}}
        │
        ▼  (if P(coffee) >= 0.75)
  YOLODetectorService  (vision/core/detection/service.py)
        │
        ▼
  ONNXDetectionEngine  (vision/core/detection/engines/onnx_engine.py)
    loads:  vision/model/best.onnx          (YOLOv8n, 12.8 MB)
            vision/model/classes.json       (defect class manifest)
        │
        ▼
  Preprocessing → ONNX Runtime → Postprocessing → NMS → Annotation
        │
        ▼
  200 OK — YOLODetectionResult (both model versions, coffee confidence, defect counts & boxes)
```

### Key design decisions already made

- **Fail-loud at startup** — if either ONNX model, either model configuration, or a model output shape is invalid, the service refuses to start. No silent mock or demo fallback.
- **Each engine instance owns its class manifest** — loaded at instantiation, not as a module-level singleton, so hot-reload works correctly.
- **Versioned model bundle** — successful detection responses include separate YOLO and validator versions. Hot reload swaps both models together only after both load successfully.
- **Bare Base64** in API — the `/detect` endpoint accepts raw Base64 (no `data:image/jpeg;base64,` prefix). The contract example in `contracts/vision-api/examples/detection_success.json` reflects this.
- **`anyio.to_thread.run_sync`** wraps blocking ONNX calls in `main.py` — keeps FastAPI async-safe.

---

## Current Folder Structure

```
vision/
├── AGENTS.md                          ← architecture invariants and rules (read this first)
├── PROJECT_STATE.md                   ← this file
├── Dockerfile
├── .dockerignore
├── pytest.ini
├── requirements.txt
│
├── core/
│   ├── schemas.py                     ← shared Pydantic schemas (DetectionResponse, etc.)
│   └── detection/
│       ├── __init__.py
│       ├── config.py                  ← path constants and runtime config
│       ├── labels.py                  ← fail-loud manifest loader (classes.json → dict)
│       ├── validator.py               ← MobileNetV3 coffee-domain validation
│       ├── annotator.py               ← draws bounding boxes onto image
│       ├── preprocessing.py           ← resize + normalize image for ONNX input
│       ├── postprocessing.py          ← decode ONNX output, apply NMS
│       ├── service.py                 ← YOLODetectorService: orchestrates the pipeline
│       └── engines/
│           ├── __init__.py
│           ├── base.py                ← abstract DetectionEngine interface
│           ├── factory.py             ← creates the right engine from config
│           ├── onnx_engine.py         ← ONNXDetectionEngine (production)
│           └── torch_engine.py        ← retained legacy code; not used for serving
│
├── model/
│   ├── README.md                      ← model card
│   ├── best.onnx                      ← YOLOv8n defect detector (12.8 MB)
│   ├── best_validator.onnx            ← MobileNetV3-Small domain validator (6.09 MB)
│   ├── best.pt                        ← PyTorch source weights (6.5 MB)
│   ├── classes.json                   ← defect class manifest with model_version field
│   └── validator_config.json          ← validator labels, threshold, and model version
│
├── service/
│   ├── __init__.py
│   └── main.py                        ← FastAPI app: /health, /detect, /reload-model
│
├── tests/
│   ├── __init__.py
│   ├── test_yolo_detector.py          ← detector and endpoint tests
│   ├── test_detection_modules.py      ← preprocessing, manifest, and reload tests
│   └── test_validator.py              ← domain validation and startup tests
│
├── evaluation/
│   ├── 30_174.jpg                     ← golden regression image (has defects)
│   ├── 30_175.jpg                     ← golden regression image (has defects)
│   └── 30_269.jpg                     ← golden regression image (different defect pattern)
│
└── training/
    ├── train_coffee_validator.ipynb  ← Colab notebook used to train best_validator.onnx
    └── train_yolov8_coffee.ipynb      ← Colab notebook used to train best.onnx
```

---

## Completed Features

### Coffee Domain Validator

The YOLO defect detector is a closed-world model, so a separate binary ONNX classifier checks
whether an image contains coffee before defect inference runs.

Images below the configured coffee-confidence threshold are rejected with HTTP 400. Accepted images
continue to YOLO inference.

The validator is MobileNetV3-Small and reads its labels, confidence threshold, preprocessing
settings, and model version from `vision/model/validator_config.json`.

The HTTP response includes `model_version` for YOLO and `validator_version` for the domain model.
Hot reload loads both model/config pairs before atomically swapping the active bundle; any failure
retains both previously active models.

```
POST /detect (multipart/form-data image)
        │
        ▼
  DomainValidator  (vision/core/detection/validator.py)
    loads:  vision/model/best_validator.onnx
            vision/model/validator_config.json
        │
        ├── P(coffee) < threshold ──► HTTP 400 IMAGE_NOT_COFFEE
        ▼
  YOLODetectorService  → ONNXDetectionEngine
        │
        ▼
  200 OK — YOLODetectionResult with both model versions
```

Implemented components:

| File | Purpose |
|:-----|:--------|
| `vision/core/detection/validator.py` | ONNX runtime wrapper and domain validation |
| `vision/core/detection/service.py` | Paired model bundle, validation, and safe reload |
| `vision/model/best_validator.onnx` | Trained binary classifier weights |
| `vision/model/validator_config.json` | Labels, threshold, preprocessing, and version |
| `vision/tests/test_validator.py` | Domain acceptance/rejection and startup tests |
| `vision/training/train_coffee_validator.ipynb` | MobileNetV3-Small training and export |

---

## Constraints for Agents

1. **Never push to `main`.** All work goes to branch `vision` only.
2. **Scope:** only touch files inside `vision/` and `contracts/vision-api/`. Do not touch
   `backend/`, `frontend/`, or root files unless explicitly instructed.
3. **Service layer stays thin.** No detection or validation logic in `vision/service/main.py`.
   All logic lives in `vision/core/`.
4. **Fail-loud.** If either ONNX model or its configuration is missing or invalid at startup,
   the service must refuse to start.
5. **No decorative comments.** No ASCII banners, no `===` separators, no `# ---` dividers.
   Functional, concise docstrings only.
6. **Python environment:** `D:\Coding\Hackathon\.venv\Scripts\python.exe` (Python 3.13).
7. **Run tests before committing:** `cd D:\Coding\BunaVision-clean\vision && python -m pytest tests/ -v`

---

## Git State

- **Active branch:** `vision`
- **Remote:** `https://github.com/worku404/BunaVision.git`
- **`main` branch:** untouched at `6abe6f3` — do not touch it
- **Commits on `vision` ahead of `main`:**
  1. `9232671` — `feat(vision): refactor detection pipeline into pure ONNX modular architecture`
  2. `1afdb93` — `fix(vision): eliminate manifest fallback, dynamic bundle reload, add golden regression and lifespan tests`
  3. `6ec6df0` — `fix(vision): sync OpenAPI contract, bare Base64 example, Dockerfile and .dockerignore`
  4. `b8b7b20` — `docs: align vision documentation with pure ONNX pipeline and test coverage`

---

## Docker

- **Image:** `bunavision-vision:latest`
- **Container name:** `bunavision-detector`
- **Port:** `9000` (host) → `8000` (container)
- **Start:** `docker start bunavision-detector`
- **Rebuild:** `docker build -t bunavision-vision:latest D:\Coding\BunaVision-clean\vision`

---

*Last updated: 2026-10-22. The validator feature and paired model reload are implemented.*
