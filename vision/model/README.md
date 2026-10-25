# Vision Model Artifacts

The serving pipeline loads two ONNX models:

| Artifact | Purpose | Version source |
|---|---|---|
| `best_validator.onnx` | MobileNetV3-Small coffee / non-coffee domain classifier; 224×224 RGB input, two logits | `validator_config.json` |
| `best.onnx` | YOLOv8n detector for Full Black, Partial Black, and Coffee Husk / Parchment; 640×640 RGB input | `classes.json` |

`validator_config.json` defines the validator class order, coffee class index, confidence threshold, preprocessing values, and `model_version`. `classes.json` maps YOLO class IDs to raw dataset labels and defines the YOLO model version.

`best.pt` is retained as a training checkpoint only; serving uses ONNX Runtime for both stages.

## Startup and Reload

At startup, the service loads and validates both ONNX models and both configuration files. It refuses to start if an artifact is missing, invalid, or has an incompatible output shape. The validator output must have one logit per configured label; the detector output must contain four box coordinates and one score per configured defect class.

`POST /reload-model` builds a new model bundle and swaps it in only after both models load successfully. If either load fails, the active bundle remains in use.

No mock or synthetic inference fallback is used.
