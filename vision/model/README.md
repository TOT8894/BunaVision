# Vision Model Artifacts

This directory stores trained weights and class manifests for defect detection:

- **best.onnx**: Production ONNX Runtime weights (CPU inference, 640x640).
- **best.pt**: PyTorch / Ultralytics fallback checkpoint.
- **classes.json**: Defect class manifest mapping IDs to labels.

### Model Loading
1. The service looks for `best.onnx` first, then falls back to `best.pt`.
2. Model loading is verified during service startup. If no weights are found, the service fails fast with an error. No mock or synthetic output is generated.
