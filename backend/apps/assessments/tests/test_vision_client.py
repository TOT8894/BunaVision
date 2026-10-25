"""Focused contract tests for the synchronous Vision adapter.

The payloads mirror the FastAPI backend's Vision client fixtures. No Django database,
application startup, or external service is needed for these tests.
"""

import unittest
from unittest import mock

import httpx

from apps.assessments.clients import vision
from apps.assessments.image_validation import ImageFormat, ValidatedImage
from apps.common.errors import NotCoffeeImage, VisionBadResponse, VisionTimeout, VisionUnavailable
from apps.common.logging import request_id_var


class VisionClientContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.image = ValidatedImage(
            data=b"image-bytes", format=ImageFormat.JPEG, width=320, height=320
        )

    def _detect(self, response_handler):
        client = httpx.Client(
            base_url="http://vision.test",
            transport=httpx.MockTransport(response_handler),
        )
        with client, mock.patch.object(vision, "get_http_client", return_value=client):
            return vision.detect(self.image)

    def test_success_uses_fastapi_request_and_accepts_vision_extra_fields(self) -> None:
        payload = {
            "model_version": "YOLOv8n-Coffee-ONNX-v1",
            "validator_version": "MobileNetV3-Small-Coffee-ONNX-v1",
            "is_coffee": True,
            "coffee_confidence": 0.99,
            "total_beans": 1,
            "healthy_beans": -1,
            "defect_beans": 1,
            "detected_beans": [
                {
                    "box": {"x1": 1, "y1": 2, "x2": 30, "y2": 40},
                    "class_name": "Full Black",
                    "confidence": 0.9,
                    "category": "Primary Defect",
                }
            ],
            "annotated_image_base64": None,
        }
        observed = {}

        def respond(request: httpx.Request) -> httpx.Response:
            observed["method"] = request.method
            observed["path"] = request.url.path
            observed["request_id"] = request.headers.get("X-Request-ID")
            observed["multipart"] = 'name="file"' in request.content.decode("latin-1")
            observed["neutral_filename"] = 'filename="upload.jpg"' in request.content.decode("latin-1")
            return httpx.Response(200, json=payload)

        token = request_id_var.set("vision-contract-test")
        try:
            result = self._detect(respond)
        finally:
            request_id_var.reset(token)

        self.assertEqual(
            observed,
            {
                "method": "POST",
                "path": "/detect",
                "request_id": "vision-contract-test",
                "multipart": True,
                "neutral_filename": True,
            },
        )
        self.assertEqual(result.model_version, payload["model_version"])
        self.assertEqual(result.validator_version, payload["validator_version"])
        self.assertEqual(result.coffee_confidence, 0.99)
        self.assertEqual(len(result.detections), 1)

    def test_zero_detections_are_a_valid_success(self) -> None:
        payload = {
            "model_version": "model-v1",
            "validator_version": "validator-v1",
            "is_coffee": True,
            "coffee_confidence": 0.99,
            "total_beans": 0,
            "healthy_beans": -1,
            "defect_beans": 0,
            "detected_beans": [],
            "annotated_image_base64": None,
        }
        result = self._detect(lambda _: httpx.Response(200, json=payload))
        self.assertEqual(result.detections, ())

    def test_fastapi_400_non_coffee_envelope_maps_to_client_error(self) -> None:
        rejection = {
            "detail": {
                "code": "IMAGE_NOT_COFFEE",
                "message": "not coffee",
                "confidence": 0.02,
                "threshold": 0.75,
            }
        }
        with self.assertRaises(NotCoffeeImage) as caught:
            self._detect(lambda _: httpx.Response(400, json=rejection))
        self.assertEqual(
            caught.exception.details,
            {"is_coffee": False, "coffee_confidence": 0.02, "threshold": 0.75},
        )

    def test_200_false_coffee_is_mapped_before_any_assessment_result(self) -> None:
        payload = {
            "model_version": "model-v1",
            "validator_version": "validator-v1",
            "is_coffee": False,
            "coffee_confidence": 0.02,
            "total_beans": 0,
            "healthy_beans": -1,
            "defect_beans": 0,
            "detected_beans": [],
            "annotated_image_base64": None,
        }
        with self.assertRaises(NotCoffeeImage) as caught:
            self._detect(lambda _: httpx.Response(200, json=payload))
        self.assertEqual(caught.exception.details["coffee_confidence"], 0.02)

    def test_missing_fields_and_malformed_success_bodies_are_bad_responses(self) -> None:
        missing_required = {
            "model_version": "model-v1",
            "total_beans": 0,
            "detected_beans": [],
        }
        malformed_detection = {
            "model_version": "model-v1",
            "validator_version": "validator-v1",
            "is_coffee": True,
            "coffee_confidence": 0.99,
            "detected_beans": [
                {
                    "box": {"x1": 4, "y1": 2, "x2": 1, "y2": 3},
                    "class_name": "Full Black",
                    "confidence": 1.2,
                }
            ],
        }
        for body in (missing_required, malformed_detection):
            with self.subTest(body=body), self.assertRaises(VisionBadResponse):
                self._detect(lambda _, payload=body: httpx.Response(200, json=payload))

        with self.assertRaises(VisionBadResponse):
            self._detect(lambda _: httpx.Response(200, content=b"not-json"))

    def test_http_errors_and_timeouts_keep_fastapi_error_mapping(self) -> None:
        with self.assertRaises(VisionUnavailable):
            self._detect(lambda _: httpx.Response(500, json={"detail": "failed"}))

        def timeout(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timed out", request=request)

        with self.assertRaises(VisionTimeout):
            self._detect(timeout)


if __name__ == "__main__":
    unittest.main()
