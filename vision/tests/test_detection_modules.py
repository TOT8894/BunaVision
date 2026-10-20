import io
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import numpy as np
from PIL import Image

from vision.core.detection import (
    YOLODetectorService,
    get_detector,
    SUPPORTED_CLASSES,
    classify_category,
    nms,
)
from vision.core.detection.config import (
    DEFAULT_IMG_SIZE,
    MODEL_VERSION,
)
from vision.core.detection.labels import (
    load_class_manifest,
    load_class_mapping,
    get_supported_classes,
)
from vision.core.detection.preprocessing import (
    prepare_image,
    preprocess_for_onnx,
)
from vision.core.detection.postprocessing import rescale_boxes
from vision.core.detection.annotator import annotate_image, get_annotation_style
from vision.core.detection.engines.base import RawDetection
from vision.core.detection.engines.factory import create_engine
from vision.core.detection.engines.onnx_engine import ONNXDetectionEngine
from vision.core.schemas import DetectedBean, BoundingBox

class DummyEngine:
    model_version = "DummyEngine-v1"
    engine_type = "dummy"
    is_loaded = True
    supported_classes = ["Full Black", "Partial Black"]
    class_mapping = {0: "hitam", 1: "hitam-sebagian"}

    def predict(self, pil_img, conf_threshold):
        return [
            RawDetection(
                x1=50.0,
                y1=50.0,
                x2=100.0,
                y2=100.0,
                confidence=0.88,
                class_id=0,
                class_name="hitam",
            )
        ]

def test_dummy_engine_injection():
    engine = DummyEngine()
    service = YOLODetectorService(engine=engine)
    assert service.is_loaded is True
    assert service.engine_type == "dummy"
    assert service.model_version == "DummyEngine-v1"
    assert service.supported_classes == ["Full Black", "Partial Black"]

    img = Image.new("RGB", (200, 200), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    result = service.detect(buf.getvalue())
    assert result.model_version == "DummyEngine-v1"
    assert result.defect_beans == 1
    assert result.total_beans == 1
    assert result.detected_beans[0].class_name == "Full Black"
    assert result.detected_beans[0].category == "Primary Defect"
    assert result.annotated_image_base64 is not None

def test_preprocess_for_onnx_letterbox():
    img = Image.new("RGB", (800, 400), color=(50, 50, 50))
    tensor, meta = preprocess_for_onnx(img)
    orig_w, orig_h, scale, pad_left, pad_top = meta

    assert tensor.shape == (1, 3, DEFAULT_IMG_SIZE, DEFAULT_IMG_SIZE)
    assert orig_w == 800
    assert orig_h == 400
    assert scale == 640 / 800
    assert pad_left == 0
    assert pad_top == (640 - int(400 * 0.8)) // 2
    assert tensor.dtype == np.float32

def test_rescale_boxes_letterbox():
    meta = (800, 400, 0.8, 0, 160)
    cxcywh = np.array([[320.0, 320.0, 160.0, 80.0]])
    xyxy = rescale_boxes(cxcywh, meta)
    assert np.allclose(xyxy[0], [300.0, 150.0, 500.0, 250.0])

def test_annotate_image():
    img = Image.new("RGB", (200, 200), color=(200, 200, 200))
    beans = [
        DetectedBean(
            box=BoundingBox(x1=10, y1=10, x2=50, y2=50),
            class_name="Full Black",
            confidence=0.95,
            category="Primary Defect",
        )
    ]
    b64 = annotate_image(img, beans)
    assert isinstance(b64, str)
    assert len(b64) > 100

def test_create_engine_missing_model_raises():
    with patch("vision.core.detection.engines.onnx_engine.MODEL_ONNX_PATH", Path("non_existent_weights.onnx")):
        with pytest.raises(RuntimeError) as exc_info:
            create_engine()
        assert "Failed to load ONNX model" in str(exc_info.value)

def test_reload_failure_retains_active_engine():
    service = YOLODetectorService()
    active_engine = service.engine
    assert service.is_loaded is True

    # Simulate reload failure (e.g. invalid weights during hot-reload)
    with patch("vision.core.detection.service.create_engine", side_effect=RuntimeError("Corrupt weights")):
        success = service.reload_model()
        assert success is False
        # Active engine must be preserved
        assert service.engine is active_engine
        assert service.is_loaded is True

def test_onnx_invalid_output_shape_fails():
    mock_session = MagicMock()
    mock_out = MagicMock()
    # 2D output instead of expected 3D [1, 7, 8400]
    mock_out.shape = [1, 100]
    mock_session.get_outputs.return_value = [mock_out]

    with patch("onnxruntime.InferenceSession", return_value=mock_session):
        engine = ONNXDetectionEngine()
        assert engine.is_loaded is False

def test_manifest_missing_raises_no_silent_fallback():
    # Enforce fail-fast: if manifest file does not exist, loud failure without fallback
    non_existent = Path("non_existent_classes_manifest.json")
    with pytest.raises(FileNotFoundError) as exc:
        load_class_manifest(non_existent)
    assert "Class manifest file not found" in str(exc.value)

    with pytest.raises(FileNotFoundError):
        load_class_mapping(non_existent)

def test_manifest_invalid_json_raises():
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        f.write("{ invalid json")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError) as exc:
            load_class_manifest(temp_path)
        assert "Corrupt or invalid JSON" in str(exc.value)
    finally:
        if temp_path.exists():
            temp_path.unlink()

def test_manifest_missing_names_key_raises():
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"num_classes": 3}, f)
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError) as exc:
            load_class_manifest(temp_path)
        assert "missing or invalid 'names' mapping" in str(exc.value)
    finally:
        if temp_path.exists():
            temp_path.unlink()

def test_reload_model_updates_metadata_and_classes():
    service = YOLODetectorService()
    initial_version = service.model_version
    assert initial_version == "YOLOv8n-Coffee-ONNX-v1"

    new_manifest_data = {
        "num_classes": 3,
        "names": {
            "0": "hitam",
            "1": "hitam-sebagian",
            "2": "kulit-kopi-kecil",
        },
        "model_version": "YOLOv8n-Coffee-ONNX-v2-Experimental",
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(new_manifest_data, f)
        temp_manifest = Path(f.name)

    try:
        success = service.reload_model(manifest_path=temp_manifest)
        assert success is True
        assert service.model_version == "YOLOv8n-Coffee-ONNX-v2-Experimental"
        assert service.supported_classes == ["Full Black", "Partial Black", "Coffee Husk / Parchment"]
    finally:
        if temp_manifest.exists():
            temp_manifest.unlink()
        # Restore original engine state
        service.reload_model()
