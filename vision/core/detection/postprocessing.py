from typing import List, Optional, Tuple
import numpy as np
from vision.core.detection.config import DEFAULT_IOU_THRESHOLD

def _single_class_nms(
    boxes: np.ndarray,
    scores: np.ndarray,
    iou_threshold: float = DEFAULT_IOU_THRESHOLD,
) -> List[int]:
    if len(boxes) == 0:
        return []

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = np.maximum(0.0, x2 - x1) * np.maximum(0.0, y2 - y1)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h

        union = areas[i] + areas[order[1:]] - inter
        iou = inter / np.maximum(union, 1e-6)

        inds = np.where(iou <= iou_threshold)[0]
        order = order[inds + 1]

    return keep

def nms(
    boxes: np.ndarray,
    scores: np.ndarray,
    iou_threshold: float = DEFAULT_IOU_THRESHOLD,
    class_ids: Optional[np.ndarray] = None,
) -> List[int]:
    if len(boxes) == 0:
        return []

    # If class_ids provided, run per-class NMS so different classes never suppress each other
    if class_ids is not None:
        keep = []
        for cls_id in np.unique(class_ids):
            cls_mask = np.where(class_ids == cls_id)[0]
            cls_keep = _single_class_nms(boxes[cls_mask], scores[cls_mask], iou_threshold)
            keep.extend(cls_mask[cls_keep].tolist())
        # Sort surviving detections by score descending
        keep.sort(key=lambda idx: scores[idx], reverse=True)
        return keep

    return _single_class_nms(boxes, scores, iou_threshold)

def rescale_boxes(
    raw_cxcywh: np.ndarray,
    meta: Tuple[int, int, float, int, int]
) -> np.ndarray:
    orig_w, orig_h, scale, pad_left, pad_top = meta

    cx = raw_cxcywh[:, 0]
    cy = raw_cxcywh[:, 1]
    w = raw_cxcywh[:, 2]
    h = raw_cxcywh[:, 3]

    x1_canvas = cx - w / 2.0
    y1_canvas = cy - h / 2.0
    x2_canvas = cx + w / 2.0
    y2_canvas = cy + h / 2.0

    x1 = np.clip((x1_canvas - pad_left) / scale, 0, orig_w)
    y1 = np.clip((y1_canvas - pad_top) / scale, 0, orig_h)
    x2 = np.clip((x2_canvas - pad_left) / scale, 0, orig_w)
    y2 = np.clip((y2_canvas - pad_top) / scale, 0, orig_h)

    return np.column_stack([x1, y1, x2, y2])
