from vision.core.detection.config import (
    MODEL_DIR,
    MODEL_ONNX_PATH,
    MODEL_PT_PATH,
)
from vision.core.detection.labels import (
    ONNX_CLASSES,
    CLASS_NAME_MAP,
    CLASS_COLORS,
    PRIMARY_DEFECT_CLASSES,
    SECONDARY_DEFECT_CLASSES,
    SUPPORTED_CLASSES,
    classify_category,
)
from vision.core.detection.postprocessing import nms
from vision.core.detection.annotator import get_annotation_style as _get_annotation_style
from vision.core.detection.service import YOLODetectorService, get_detector

MODEL_PATH = MODEL_ONNX_PATH

# Backward-compatible singleton proxy
yolo_service = get_detector()

__all__ = [
    "yolo_service",
    "get_detector",
    "YOLODetectorService",
    "nms",
    "classify_category",
    "SUPPORTED_CLASSES",
    "MODEL_PATH",
    "MODEL_DIR",
    "MODEL_ONNX_PATH",
    "MODEL_PT_PATH",
    "ONNX_CLASSES",
    "CLASS_NAME_MAP",
    "CLASS_COLORS",
    "PRIMARY_DEFECT_CLASSES",
    "SECONDARY_DEFECT_CLASSES",
    "_get_annotation_style",
]
