import io
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from vision.core.yolo_detector import (
    yolo_service,
    nms,
    _get_annotation_style,
    SUPPORTED_CLASSES,
)
from vision.service.main import app

client = TestClient(app)

def test_classify_category_exact_matching():
    # Raw Roboflow labels
    assert yolo_service.classify_category("hitam") == "Primary Defect"
    assert yolo_service.classify_category("hitam-sebagian") == "Secondary Defect"
    assert yolo_service.classify_category("kulit-kopi-kecil") == "Secondary Defect"

    # Canonical English labels
    assert yolo_service.classify_category("Full Black") == "Primary Defect"
    assert yolo_service.classify_category("Partial Black") == "Secondary Defect"
    assert yolo_service.classify_category("Coffee Husk / Parchment") == "Secondary Defect"

    # Unknown classes must raise ValueError (no silent fabrications)
    with pytest.raises(ValueError) as exc:
        yolo_service.classify_category("unsupported_defect")
    assert "Unsupported defect class" in str(exc.value)

def test_nms_suppression():
    boxes = np.array([
        [10.0, 10.0, 50.0, 50.0],
        [11.0, 11.0, 50.0, 50.0],
    ])
    scores = np.array([0.9, 0.7])
    keep = nms(boxes, scores, iou_threshold=0.45)
    assert keep == [0]

def test_nms_different_boxes():
    boxes = np.array([
        [10.0, 10.0, 50.0, 50.0],
        [100.0, 100.0, 150.0, 150.0],
    ])
    scores = np.array([0.85, 0.80])
    keep = nms(boxes, scores, iou_threshold=0.45)
    assert len(keep) == 2

def test_nms_class_aware_keeps_different_classes():
    boxes = np.array([
        [10.0, 10.0, 50.0, 50.0],
        [12.0, 12.0, 52.0, 52.0],
    ])
    scores = np.array([0.9, 0.85])

    keep_agnostic = nms(boxes, scores, iou_threshold=0.45, class_ids=None)
    assert len(keep_agnostic) == 1

    class_ids = np.array([0, 1])
    keep_aware = nms(boxes, scores, iou_threshold=0.45, class_ids=class_ids)
    assert len(keep_aware) == 2

def test_nms_class_aware_suppresses_same_class():
    boxes = np.array([
        [10.0, 10.0, 50.0, 50.0],
        [12.0, 12.0, 52.0, 52.0],
    ])
    scores = np.array([0.9, 0.85])
    class_ids = np.array([0, 0])
    keep = nms(boxes, scores, iou_threshold=0.45, class_ids=class_ids)
    assert len(keep) == 1

def test_nms_high_res_coordinates_no_collision():
    # High-resolution image (4032x3024) coordinates exceeding 4096px
    boxes = np.array([
        [4100.0, 2000.0, 4200.0, 2100.0],
        [4102.0, 2002.0, 4202.0, 2102.0],
    ])
    scores = np.array([0.92, 0.88])
    class_ids = np.array([0, 1])

    # Per-class NMS keeps both because they belong to different classes
    keep = nms(boxes, scores, iou_threshold=0.45, class_ids=class_ids)
    assert len(keep) == 2

def test_nms_empty_input():
    boxes = np.array([]).reshape(0, 4)
    scores = np.array([])
    assert nms(boxes, scores) == []

def test_supported_classes_matches_trained_model():
    assert len(SUPPORTED_CLASSES) == 3
    assert "Full Black" in SUPPORTED_CLASSES
    assert "Partial Black" in SUPPORTED_CLASSES
    assert "Coffee Husk / Parchment" in SUPPORTED_CLASSES

def test_annotation_style_scales_with_image_size():
    font_small, stroke_small = _get_annotation_style((640, 640))
    font_large, stroke_large = _get_annotation_style((4032, 3024))
    assert stroke_large >= stroke_small

def test_detect_blank_image_zero_defects():
    img = Image.new("RGB", (640, 640), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    result = yolo_service.detect(buf.getvalue(), validate_domain=False)
    assert result.model_version == "YOLOv8n-Coffee-ONNX-v1"
    assert result.total_beans == 0
    assert result.defect_beans == 0
    assert result.healthy_beans == -1
    assert result.detected_beans == []
    assert result.annotated_image_base64 is None

def test_detect_returns_model_version():
    img = Image.new("RGB", (640, 640), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    result = yolo_service.detect(buf.getvalue(), validate_domain=False)
    assert result.model_version is not None
    assert len(result.model_version) > 0
    assert result.validator_version == yolo_service.validator_version

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["engine"] == "onnx"
    assert data["supported_classes"] == SUPPORTED_CLASSES
    assert "model_path" in data

def test_detect_endpoint_success():
    golden_path = Path(__file__).resolve().parent.parent / "evaluation" / "30_174.jpg"
    assert golden_path.exists(), f"Golden image missing: {golden_path}"

    response = client.post(
        "/detect",
        files={"file": ("30_174.jpg", golden_path.read_bytes(), "image/jpeg")},
        params={"confidence": 0.25}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model_version"] == "YOLOv8n-Coffee-ONNX-v1"
    assert data["validator_version"] == "MobileNetV3-Small-Coffee-ONNX-v1"
    assert data["is_coffee"] is True
    assert data["total_beans"] > 0
    assert data["healthy_beans"] == -1
    assert data["defect_beans"] > 0

def test_detect_endpoint_empty_file():
    response = client.post(
        "/detect",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert "Empty image" in response.json()["detail"]

def test_detect_endpoint_corrupted_file():
    response = client.post(
        "/detect",
        files={"file": ("corrupt.jpg", b"not-an-image-payload", "image/jpeg")}
    )
    assert response.status_code == 400
    assert "Invalid image file" in response.json()["detail"]

def test_detect_endpoint_unsupported_format():
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="GIF")

    response = client.post(
        "/detect",
        files={"file": ("sample.gif", buf.getvalue(), "image/gif")}
    )
    assert response.status_code == 415
    assert "Unsupported image format" in response.json()["detail"]

def test_reload_model_endpoint():
    response = client.post("/reload-model")
    assert response.status_code == 200
    data = response.json()
    assert data["reloaded"] is True
    assert data["engine"] == "onnx"

def test_lifespan_fail_fast_on_unloaded_model():
    mock_detector = MagicMock()
    mock_detector.is_loaded = False
    with patch("vision.service.main.get_detector", return_value=mock_detector):
        with pytest.raises(RuntimeError) as exc_info:
            with TestClient(app):
                pass
        assert "YOLO ONNX model failed to load at startup" in str(exc_info.value)

@pytest.mark.parametrize("img_name,expected_min_defects", [
    ("30_174.jpg", 3),
    ("30_175.jpg", 2),
    ("30_269.jpg", 3),
])
def test_golden_image_evaluation_regression(img_name: str, expected_min_defects: int):
    golden_path = Path(__file__).parent.parent / "evaluation" / img_name
    assert golden_path.exists(), f"Evaluation golden image {img_name} missing from vision/evaluation"
    img_bytes = golden_path.read_bytes()

    # 1. Direct detector service evaluation
    result = yolo_service.detect(img_bytes, confidence_threshold=0.25)
    assert result.model_version == "YOLOv8n-Coffee-ONNX-v1"
    assert result.defect_beans >= expected_min_defects
    assert result.total_beans >= expected_min_defects
    assert result.annotated_image_base64 is not None

    # Validate that annotated base64 payload is valid JPEG
    decoded_bytes = base64.b64decode(result.annotated_image_base64)
    with Image.open(io.BytesIO(decoded_bytes)) as annotated_img:
        assert annotated_img.format == "JPEG"

    # Validate bounding boxes, confidence scores and defect taxonomy
    with Image.open(io.BytesIO(img_bytes)) as original:
        orig_w, orig_h = original.size

    for bean in result.detected_beans:
        assert bean.class_name in yolo_service.supported_classes
        assert bean.category in {"Primary Defect", "Secondary Defect"}
        assert 0.25 <= bean.confidence <= 1.0
        assert 0.0 <= bean.box.x1 < bean.box.x2 <= orig_w + 5.0
        assert 0.0 <= bean.box.y1 < bean.box.y2 <= orig_h + 5.0

    # 2. FastAPI endpoint regression test
    response = client.post(
        "/detect",
        files={"file": (img_name, img_bytes, "image/jpeg")},
        params={"confidence": 0.25}
    )
    assert response.status_code == 200
    api_data = response.json()
    assert api_data["defect_beans"] >= expected_min_defects
    assert len(api_data["detected_beans"]) >= expected_min_defects
