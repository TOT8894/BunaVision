import io
import functools
import logging
from pathlib import Path
from typing import Optional, List, Dict
from PIL import Image

from vision.core.schemas import (
    BoundingBox,
    DetectedBean,
    YOLODetectionResult,
)
from vision.core.detection.config import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    MODEL_DIR,
)
from vision.core.detection.labels import (
    classify_category,
    get_display_name,
    SUPPORTED_CLASSES,
)
from vision.core.detection.preprocessing import prepare_image
from vision.core.detection.annotator import annotate_image
from vision.core.detection.engines.base import DetectionEngine
from vision.core.detection.engines.factory import create_engine

logger = logging.getLogger("bunavision.detector")

class YOLODetectorService:
    def __init__(self, engine: Optional[DetectionEngine] = None):
        self.engine = engine if engine is not None else create_engine()

    @property
    def engine_type(self) -> str:
        return self.engine.engine_type

    @property
    def is_loaded(self) -> bool:
        return self.engine.is_loaded

    @property
    def model_version(self) -> str:
        return self.engine.model_version

    @property
    def model_path(self):
        return getattr(self.engine, "model_path", None)

    @property
    def supported_classes(self) -> List[str]:
        return getattr(self.engine, "supported_classes", SUPPORTED_CLASSES)

    @property
    def class_mapping(self) -> Dict[int, str]:
        return getattr(self.engine, "class_mapping", {})

    def reload_model(
        self,
        model_path: Optional[Path] = None,
        manifest_path: Optional[Path] = None,
        model_version: Optional[str] = None,
    ) -> bool:
        # Safe swap: only replace working engine if new engine loads successfully
        try:
            new_engine = create_engine(
                model_path=model_path,
                manifest_path=manifest_path,
                model_version=model_version,
            )
            if new_engine.is_loaded:
                self.engine = new_engine
                logger.info(
                    f"Model reload succeeded, new engine active "
                    f"(version={new_engine.model_version}, classes={self.supported_classes})"
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Model reload failed, retaining active engine: {e}")
            return False

    def classify_category(self, class_name: str) -> str:
        return classify_category(class_name)

    def detect(
        self,
        image_bytes: bytes,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ) -> YOLODetectionResult:
        pil_img = prepare_image(Image.open(io.BytesIO(image_bytes)))

        if not self.is_loaded:
            raise RuntimeError(
                f"YOLO detector model is not loaded (engine={self.engine_type}). "
                f"Ensure 'best.onnx' exists in '{MODEL_DIR}'."
            )

        raw_detections = self.engine.predict(pil_img, conf_threshold=confidence_threshold)

        if len(raw_detections) == 0:
            return YOLODetectionResult(
                model_version=self.model_version,
                total_beans=0,
                healthy_beans=-1,
                defect_beans=0,
                defect_counts={},
                detected_beans=[],
                annotated_image_base64=None,
            )

        detected_beans: List[DetectedBean] = []
        counts: Dict[str, int] = {}

        for raw in raw_detections:
            display_name = get_display_name(raw.class_name)
            category = classify_category(raw.class_name)
            counts[display_name] = counts.get(display_name, 0) + 1

            detected_beans.append(
                DetectedBean(
                    box=BoundingBox(
                        x1=round(raw.x1, 1),
                        y1=round(raw.y1, 1),
                        x2=round(raw.x2, 1),
                        y2=round(raw.y2, 1),
                    ),
                    class_name=display_name,
                    confidence=round(raw.confidence, 3),
                    category=category,
                )
            )

        img_b64 = annotate_image(pil_img, detected_beans)

        return YOLODetectionResult(
            model_version=self.model_version,
            total_beans=len(detected_beans),
            healthy_beans=-1,
            defect_beans=len(detected_beans),
            defect_counts=counts,
            detected_beans=detected_beans,
            annotated_image_base64=img_b64,
        )

@functools.lru_cache(maxsize=1)
def get_detector() -> YOLODetectorService:
    return YOLODetectorService()
