import io
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from vision.core.detection.validator import (
    DomainValidator,
    ImageDomainRejectedError,
)
from vision.core.detection import YOLODetectorService, get_detector
from vision.service.main import app

EVAL_DIR = Path(__file__).resolve().parent.parent / "evaluation"


@pytest.fixture
def validator():
    return DomainValidator()


@pytest.fixture
def non_coffee_image_bytes():
    # Pure black image - distinctly non-coffee
    arr = np.zeros((300, 300, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def golden_coffee_bytes():
    golden_path = EVAL_DIR / "30_174.jpg"
    assert golden_path.exists(), f"Golden image missing: {golden_path}"
    return golden_path.read_bytes()


def test_validator_loads_and_has_correct_metadata(validator):
    assert validator.is_loaded is True
    assert validator.model_version == "MobileNetV3-Small-Coffee-ONNX-v1"
    assert validator.threshold == 0.75
    assert validator.coffee_class_index == 0


def test_validator_positive_golden_images(validator):
    golden_images = ["30_174.jpg", "30_175.jpg", "30_269.jpg"]
    for img_name in golden_images:
        path = EVAL_DIR / img_name
        if not path.exists():
            continue
        img = Image.open(path)
        result = validator.validate(img)
        assert result.is_coffee is True, f"Failed on {img_name}: {result}"
        assert result.confidence >= 0.75


def test_validator_negative_synthetic_images(validator):
    # Test black image
    black_img = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
    black_res = validator.validate(black_img)
    assert black_res.is_coffee is False
    assert black_res.confidence < 0.75

    # Test random uniform noise
    np.random.seed(42)
    noise_arr = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
    noise_img = Image.fromarray(noise_arr)
    noise_res = validator.validate(noise_img)
    assert noise_res.is_coffee is False
    assert noise_res.confidence < 0.75


def test_detector_service_rejects_non_coffee(non_coffee_image_bytes):
    service = YOLODetectorService()
    with pytest.raises(ImageDomainRejectedError) as exc_info:
        service.detect(non_coffee_image_bytes)

    assert exc_info.value.confidence < 0.75
    assert exc_info.value.threshold == 0.75


def test_detector_service_accepts_coffee(golden_coffee_bytes):
    service = YOLODetectorService()
    result = service.detect(golden_coffee_bytes)
    assert result.is_coffee is True
    assert result.coffee_confidence is not None
    assert result.coffee_confidence >= 0.75
    assert result.total_beans == -1
    assert result.defect_beans > 0


def test_api_detect_returns_400_on_non_coffee(non_coffee_image_bytes):
    with TestClient(app) as client:
        resp = client.post(
            "/detect",
            files={"file": ("test_negative.jpg", non_coffee_image_bytes, "image/jpeg")},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert "detail" in data
        assert data["detail"]["code"] == "IMAGE_NOT_COFFEE"
        assert data["detail"]["confidence"] < 0.75
        assert data["detail"]["threshold"] == 0.75


def test_api_detect_returns_200_on_coffee(golden_coffee_bytes):
    with TestClient(app) as client:
        resp = client.post(
            "/detect",
            files={"file": ("30_174.jpg", golden_coffee_bytes, "image/jpeg")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_coffee"] is True
        assert data["coffee_confidence"] >= 0.75
        assert data["total_beans"] == -1
        assert data["defect_beans"] > 0
        assert "annotated_image_base64" in data


def test_validator_missing_files_fail_loud(tmp_path):
    nonexistent_model = tmp_path / "nonexistent.onnx"
    nonexistent_config = tmp_path / "nonexistent.json"

    with pytest.raises(FileNotFoundError):
        DomainValidator(config_path=nonexistent_config)

    # Valid dummy config to test missing model
    dummy_config = tmp_path / "dummy_config.json"
    dummy_config.write_text(
        '{"model_version": "test-validator", "labels": ["coffee", "not_coffee"], '
        '"coffee_class_index": 0, '
        '"confidence_threshold": 0.75}'
    )
    with pytest.raises(FileNotFoundError):
        DomainValidator(model_path=nonexistent_model, config_path=dummy_config)


@pytest.mark.parametrize(
    "output_shape",
    [
        [1, 1],
        [1, 3],
        [2],
    ],
)
def test_validator_rejects_incompatible_output_shape(output_shape):
    mock_session = MagicMock()
    mock_output = MagicMock()
    mock_output.shape = output_shape
    mock_session.get_outputs.return_value = [mock_output]

    with patch("onnxruntime.InferenceSession", return_value=mock_session):
        with pytest.raises(ValueError, match="Invalid domain validator output shape"):
            DomainValidator()


@pytest.mark.parametrize(
    ("path_attribute", "filename", "error_message"),
    [
        (
            "DEFAULT_VALIDATOR_PATH",
            "missing_validator.onnx",
            "Domain validator model missing",
        ),
        (
            "DEFAULT_CONFIG_PATH",
            "missing_validator_config.json",
            "Domain validator config missing",
        ),
    ],
)
def test_app_startup_fails_when_validator_artifact_is_missing(
    tmp_path, path_attribute, filename, error_message
):
    get_detector.cache_clear()
    try:
        with patch(
            f"vision.core.detection.validator.{path_attribute}",
            tmp_path / filename,
        ):
            with pytest.raises(FileNotFoundError, match=error_message):
                with TestClient(app):
                    pass
    finally:
        get_detector.cache_clear()


def test_validator_rejects_incompatible_runtime_output_shape(validator):
    validator.session.run = lambda *_args, **_kwargs: [np.array([[1.0]])]

    with pytest.raises(RuntimeError, match="Invalid domain validator inference output shape"):
        validator.validate(Image.new("RGB", (224, 224)))
