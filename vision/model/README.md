# Vision Model Artifacts

This directory stores trained model weights, checkpoints, and class manifests for defect detection:

- **best.onnx**: Production ONNX Runtime weights (CPU inference, 640x640 input, 7 output channels). This is the only model executed by the serving pipeline.
- **best.pt**: PyTorch / Ultralytics checkpoint (fine-tuned YOLOv8 Nano). Retained strictly for retraining in `vision/training/train_yolov8_coffee.ipynb`; never loaded in the production serving path.
- **classes.json**: Model bundle manifest specifying defect class IDs, raw labels, model version, checkpoint name, and dataset license (`CC BY 4.0`).

### Model Loading & Validation

1. **Pure ONNX Serving**: The service loads `best.onnx` directly using ONNX Runtime CPUExecutionProvider. PyTorch and Ultralytics are excluded from the serving runtime.
2. **Fail-Fast Invariant**: During startup and hot-reload, the engine validates that `best.onnx` and `classes.json` exist and that the ONNX output tensor dimensions match the expected shape (`[1, 7, 8400]`). If weights or manifests are missing or corrupted, the service fails fast with an explicit error.
3. **No Mock Fallback**: The service never serves fabricated detections or falls back to synthetic mock data.
