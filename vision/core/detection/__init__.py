"""
Modular defect detection package:
- config: constants, paths, thresholds
- labels: classes, names, defect taxonomy
- preprocessing: image normalization and resizing
- postprocessing: NMS, coordinate rescaling
- annotator: visual bounding box drawing & encoding
- engines: ONNX execution backend
- service: high-level detection orchestration
"""
from vision.core.detection.service import YOLODetectorService, get_detector
from vision.core.detection.labels import SUPPORTED_CLASSES, classify_category
from vision.core.detection.postprocessing import nms

__all__ = [
    "YOLODetectorService",
    "get_detector",
    "SUPPORTED_CLASSES",
    "classify_category",
    "nms",
]
