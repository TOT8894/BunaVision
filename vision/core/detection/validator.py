import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
from PIL import Image

from vision.core.detection.config import (
    MODEL_DIR,
)

logger = logging.getLogger("bunavision.validator")

DEFAULT_VALIDATOR_PATH = MODEL_DIR / "best_validator.onnx"
DEFAULT_CONFIG_PATH = MODEL_DIR / "validator_config.json"


@dataclass
class DomainValidationResult:
    is_coffee: bool
    confidence: float
    threshold: float


class ImageDomainRejectedError(ValueError):
    """Raised when an uploaded image fails domain validation (not green coffee beans)."""

    def __init__(self, confidence: float, threshold: float, message: Optional[str] = None):
        self.confidence = confidence
        self.threshold = threshold
        self.message = (
            message
            or f"Uploaded image does not appear to contain green coffee beans (confidence {confidence:.2f} < {threshold:.2f})."
        )
        super().__init__(self.message)


class DomainValidator:
    """
    Binary domain validator for green coffee bean imagery.
    Scores an image with MobileNetV3-Small ONNX classifier to verify
    whether the input contains green coffee beans.
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        config_path: Optional[Path] = None,
    ):
        self.model_path = model_path or DEFAULT_VALIDATOR_PATH
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.session = None
        self.is_loaded = False
        self.config = {}
        self.model_version = ""
        self.labels: Tuple[str, ...] = ()
        self.coffee_class_index = 0
        self.threshold = 0.75
        self.input_size: Tuple[int, int] = (224, 224)
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

        self._load_config()
        self._load_model()

    def _load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Domain validator config missing at {self.config_path}"
            )
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        model_version = self.config.get("model_version")
        if not isinstance(model_version, str) or not model_version.strip():
            raise ValueError(
                f"Invalid domain validator config at {self.config_path}: "
                "'model_version' must be a non-empty string."
            )
        self.model_version = model_version

        labels = self.config.get("labels")
        if not isinstance(labels, list) or len(labels) < 2 or any(
            not isinstance(label, str) for label in labels
        ):
            raise ValueError(
                f"Invalid domain validator config at {self.config_path}: "
                "'labels' must contain at least two class names."
            )
        self.labels = tuple(labels)
        self.coffee_class_index = int(self.config.get("coffee_class_index", 0))
        if not 0 <= self.coffee_class_index < len(self.labels):
            raise ValueError(
                f"Invalid coffee class index {self.coffee_class_index}; "
                f"expected an index from 0 to {len(self.labels) - 1}."
            )
        self.threshold = float(self.config.get("confidence_threshold", 0.75))
        size = self.config.get("input_size", [224, 224])
        self.input_size = (int(size[0]), int(size[1]))

        if "imagenet_mean" in self.config:
            self.mean = np.array(self.config["imagenet_mean"], dtype=np.float32)
        if "imagenet_std" in self.config:
            self.std = np.array(self.config["imagenet_std"], dtype=np.float32)

    def _load_model(self):
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Domain validator model missing at {self.model_path}"
            )
        import onnxruntime as ort

        logger.info(f"Loading domain validator ONNX model from {self.model_path}")
        session = ort.InferenceSession(
            str(self.model_path),
            providers=["CPUExecutionProvider"],
        )

        outputs = session.get_outputs()
        if not outputs:
            raise ValueError("Domain validator ONNX model has no output tensors.")
        output_shape = outputs[0].shape
        if len(output_shape) != 2 or output_shape[1] != len(self.labels):
            raise ValueError(
                f"Invalid domain validator output shape {output_shape}; "
                f"expected [batch, {len(self.labels)}]."
            )

        self.session = session
        self.is_loaded = True

    def preprocess(self, pil_img: Image.Image) -> np.ndarray:
        img = pil_img.convert("RGB").resize(self.input_size, Image.Resampling.BILINEAR)
        arr = np.array(img, dtype=np.float32) / 255.0
        arr = (arr - self.mean) / self.std
        # Transpose from (H, W, C) to (1, C, H, W)
        tensor = np.transpose(arr, (2, 0, 1))
        tensor = np.expand_dims(tensor, axis=0).astype(np.float32)
        return tensor

    def validate(self, pil_img: Image.Image) -> DomainValidationResult:
        if not self.is_loaded or self.session is None:
            raise RuntimeError("Domain validator model is not loaded")

        tensor = self.preprocess(pil_img)
        input_name = self.session.get_inputs()[0].name
        outputs = self.session.run(None, {input_name: tensor})
        logits_batch = outputs[0]
        if logits_batch.ndim != 2 or logits_batch.shape != (1, len(self.labels)):
            raise RuntimeError(
                f"Invalid domain validator inference output shape {logits_batch.shape}; "
                f"expected [1, {len(self.labels)}]."
            )
        logits = logits_batch[0]

        # Softmax probability calculation
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)

        coffee_prob = float(probs[self.coffee_class_index])
        is_coffee = coffee_prob >= self.threshold

        return DomainValidationResult(
            is_coffee=is_coffee,
            confidence=round(coffee_prob, 4),
            threshold=self.threshold,
        )
