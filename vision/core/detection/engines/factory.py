import logging
from vision.core.detection.config import MODEL_ONNX_PATH
from vision.core.detection.engines.base import DetectionEngine
from vision.core.detection.engines.onnx_engine import ONNXDetectionEngine

logger = logging.getLogger("bunavision.engine.factory")

def create_engine() -> DetectionEngine:
    engine = ONNXDetectionEngine()
    if not engine.is_loaded:
        raise RuntimeError(
            f"Failed to load ONNX model from {MODEL_ONNX_PATH}. "
            f"Ensure best.onnx exists in vision/model/ and is valid."
        )
    return engine
