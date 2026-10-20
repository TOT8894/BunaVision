import logging
from pathlib import Path
from typing import List, Optional
import numpy as np
from PIL import Image

from vision.core.detection.config import (
    MODEL_ONNX_PATH,
    MODEL_VERSION,
    DEFAULT_IOU_THRESHOLD,
)
from vision.core.detection.engines.base import RawDetection
from vision.core.detection.labels import ONNX_CLASSES
from vision.core.detection.preprocessing import preprocess_for_onnx
from vision.core.detection.postprocessing import nms, rescale_boxes

logger = logging.getLogger("bunavision.engine.onnx")

class ONNXDetectionEngine:
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or MODEL_ONNX_PATH
        self.model_version = MODEL_VERSION
        self.engine_type = "onnx"
        self.session = None
        self.is_loaded = False
        self._load()

    def _load(self):
        if not self.model_path.exists():
            return
        try:
            import onnxruntime as ort
            logger.info(f"Loading ONNX model from {self.model_path}")
            session = ort.InferenceSession(
                str(self.model_path),
                providers=["CPUExecutionProvider"]
            )

            # Validate model output tensor dimensions
            outputs = session.get_outputs()
            if not outputs:
                raise ValueError("ONNX model has no output tensors")

            out_shape = outputs[0].shape
            expected_channels = 4 + len(ONNX_CLASSES)
            if len(out_shape) != 3 or expected_channels not in out_shape:
                raise ValueError(
                    f"Incompatible ONNX output shape {out_shape}. "
                    f"Expected 3D tensor containing {expected_channels} channels (4 coordinates + {len(ONNX_CLASSES)} classes)."
                )

            self.session = session
            self.is_loaded = True
            logger.info("ONNX Runtime engine loaded and validated successfully")
        except Exception as e:
            logger.warning(f"Failed to load ONNX model: {e}")
            self.session = None
            self.is_loaded = False

    def predict(self, pil_img: Image.Image, conf_threshold: float) -> List[RawDetection]:
        if not self.is_loaded or self.session is None:
            raise RuntimeError(f"ONNX model is not loaded from {self.model_path}")

        tensor, meta = preprocess_for_onnx(pil_img)

        input_name = self.session.get_inputs()[0].name
        outputs = self.session.run(None, {input_name: tensor})
        preds = outputs[0][0]

        # Ensure shape is [num_proposals, 4 + num_classes] (e.g. [8400, 7])
        if preds.shape[0] < preds.shape[1]:
            preds = preds.T

        raw_boxes = preds[:, :4]
        class_scores = preds[:, 4:]

        class_ids = np.argmax(class_scores, axis=1)
        confidences = np.max(class_scores, axis=1)

        mask = confidences >= conf_threshold
        filtered_boxes = raw_boxes[mask]
        filtered_confs = confidences[mask]
        filtered_cls = class_ids[mask]

        if len(filtered_boxes) == 0:
            return []

        xyxy = rescale_boxes(filtered_boxes, meta)
        keep_indices = nms(xyxy, filtered_confs, iou_threshold=DEFAULT_IOU_THRESHOLD, class_ids=filtered_cls)

        detections: List[RawDetection] = []
        for idx in keep_indices:
            cls_id = int(filtered_cls[idx])
            # Strict validation: only report supported classes, never invent defect_N
            if cls_id not in ONNX_CLASSES:
                logger.warning(f"Discarding unmapped class ID {cls_id} from model predictions")
                continue

            coords = xyxy[idx]
            raw_name = ONNX_CLASSES[cls_id]
            detections.append(
                RawDetection(
                    x1=float(coords[0]),
                    y1=float(coords[1]),
                    x2=float(coords[2]),
                    y2=float(coords[3]),
                    confidence=float(filtered_confs[idx]),
                    class_id=cls_id,
                    class_name=raw_name,
                )
            )

        return detections
