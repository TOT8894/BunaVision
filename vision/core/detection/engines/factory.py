import logging
from pathlib import Path
from typing import Optional
from vision.core.detection.config import MODEL_ONNX_PATH
from vision.core.detection.engines.base import DetectionEngine
from vision.core.detection.engines.onnx_engine import ONNXDetectionEngine

logger = logging.getLogger("bunavision.engine.factory")

def create_engine(
    model_path: Optional[Path] = None,
    manifest_path: Optional[Path] = None,
    model_version: Optional[str] = None,
) -> DetectionEngine:
    engine = ONNXDetectionEngine(
        model_path=model_path,
        manifest_path=manifest_path,
        model_version=model_version,
    )
    if not engine.is_loaded:
        path = model_path or MODEL_ONNX_PATH
        raise RuntimeError(
            f"Failed to load ONNX model from {path}. "
            f"Ensure best.onnx exists in vision/model/ and is valid."
        )
    return engine
