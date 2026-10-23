import io
import functools
import logging
from dataclasses import dataclass
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
from vision.core.detection.validator import DomainValidator, ImageDomainRejectedError

logger = logging.getLogger("bunavision.detector")


@dataclass(frozen=True)
class _ModelBundle:
    engine: DetectionEngine
    validator: DomainValidator


class YOLODetectorService:
    def __init__(
        self,
        engine: Optional[DetectionEngine] = None,
        validator: Optional[DomainValidator] = None,
    ):
        self._models = _ModelBundle(
            engine=engine if engine is not None else create_engine(),
            validator=validator if validator is not None else DomainValidator(),
        )

    @property
    def engine(self) -> DetectionEngine:
        return self._models.engine

    @property
    def validator(self) -> DomainValidator:
        return self._models.validator

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
    def validator_version(self) -> str:
        return self.validator.model_version

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
        validator_model_path: Optional[Path] = None,
        validator_config_path: Optional[Path] = None,
    ) -> bool:
        try:
            new_engine = create_engine(
                model_path=model_path,
                manifest_path=manifest_path,
                model_version=model_version,
            )
            new_validator = DomainValidator(
                model_path=validator_model_path,
                config_path=validator_config_path,
            )
            if not new_engine.is_loaded or not new_validator.is_loaded:
                return False

            new_models = _ModelBundle(
                engine=new_engine,
                validator=new_validator,
            )
            self._models = new_models
            logger.info(
                f"Model bundle reload succeeded "
                f"(yolo_version={new_engine.model_version}, "
                f"validator_version={new_validator.model_version})"
            )
            return True
        except Exception as e:
            logger.error(f"Model bundle reload failed, retaining active models: {e}")
            return False

    def classify_category(self, class_name: str) -> str:
        return classify_category(class_name)

    def detect(
        self,
        image_bytes: bytes,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        validate_domain: bool = True,
    ) -> YOLODetectionResult:
        pil_img = prepare_image(Image.open(io.BytesIO(image_bytes)))
        models = self._models
        engine = models.engine
        validator = models.validator

        if not engine.is_loaded:
            raise RuntimeError(
                f"YOLO detector model is not loaded (engine={engine.engine_type}). "
                f"Ensure 'best.onnx' exists in '{MODEL_DIR}'."
            )

        is_coffee = True
        coffee_confidence = None
        if validate_domain:
            val_res = validator.validate(pil_img)
            is_coffee = val_res.is_coffee
            coffee_confidence = val_res.confidence
            if not is_coffee:
                raise ImageDomainRejectedError(
                    confidence=val_res.confidence,
                    threshold=val_res.threshold,
                )

        raw_detections = engine.predict(pil_img, conf_threshold=confidence_threshold)

        if len(raw_detections) == 0:
            return YOLODetectionResult(
                model_version=engine.model_version,
                validator_version=validator.model_version,
                is_coffee=is_coffee,
                coffee_confidence=coffee_confidence,
                total_beans=-1,
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
            model_version=engine.model_version,
            validator_version=validator.model_version,
            is_coffee=is_coffee,
            coffee_confidence=coffee_confidence,
            total_beans=-1,
            healthy_beans=-1,
            defect_beans=len(detected_beans),
            defect_counts=counts,
            detected_beans=detected_beans,
            annotated_image_base64=img_b64,
        )

@functools.lru_cache(maxsize=1)
def get_detector() -> YOLODetectorService:
    return YOLODetectorService()
