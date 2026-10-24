import unittest

import httpx

from app.adapters.vision_client.client import HttpVisionDetector
from app.domain.errors import (
    NotCoffeeImageError,
    VisionBadResponseError,
    VisionTimeoutError,
    VisionUnavailableError,
)
from app.services.image_validation import ImageFormat, ValidatedImage


class VisionClientContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_zero_detections_keep_gate_and_versions_and_use_contract_upload(self) -> None:
        response_body = {
            "model_version": "YOLOv8n-Coffee-ONNX-v1",
            "validator_version": "MobileNetV3-Small-Coffee-ONNX-v1",
            "is_coffee": True,
            "coffee_confidence": 0.99,
            "total_beans": 0,
            "healthy_beans": -1,
            "defect_beans": 0,
            "detected_beans": [],
            "annotated_image_base64": None,
        }
        observed: dict[str, str | bool] = {}

        def handle(request: httpx.Request) -> httpx.Response:
            observed["method"] = request.method
            observed["path"] = request.url.path
            observed["multipart_file"] = 'name="file"' in request.content.decode("latin-1")
            return httpx.Response(200, json=response_body)

        async with httpx.AsyncClient(
            base_url="http://vision", transport=httpx.MockTransport(handle)
        ) as http:
            result = await HttpVisionDetector(http=http).detect(_image())

        self.assertEqual(observed, {"method": "POST", "path": "/detect", "multipart_file": True})
        self.assertEqual(result.model_version, response_body["model_version"])
        self.assertEqual(result.image_check.validator_version, response_body["validator_version"])
        self.assertEqual(result.image_check.coffee_confidence, 0.99)
        self.assertEqual(result.detections, ())

    async def test_domain_rejection_maps_to_image_not_coffee(self) -> None:
        def handle(_: httpx.Request) -> httpx.Response:
            return httpx.Response(
                400,
                json={
                    "detail": {
                        "code": "IMAGE_NOT_COFFEE",
                        "message": "not coffee",
                        "confidence": 0.02,
                        "threshold": 0.75,
                    }
                },
            )

        async with httpx.AsyncClient(
            base_url="http://vision", transport=httpx.MockTransport(handle)
        ) as http:
            with self.assertRaises(NotCoffeeImageError) as caught:
                await HttpVisionDetector(http=http).detect(_image())

        self.assertEqual(
            caught.exception.public_details,
            {"is_coffee": False, "coffee_confidence": 0.02, "threshold": 0.75},
        )

    async def test_success_missing_gate_fields_is_a_bad_vision_response(self) -> None:
        def handle(_: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"model_version": "YOLOv8n-Coffee-ONNX-v1", "detected_beans": []},
            )

        async with httpx.AsyncClient(
            base_url="http://vision", transport=httpx.MockTransport(handle)
        ) as http:
            with self.assertRaises(VisionBadResponseError):
                await HttpVisionDetector(http=http).detect(_image())

    async def test_timeout_and_inference_failure_remain_dependency_errors(self) -> None:
        def timeout(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("vision timed out", request=request)

        async with httpx.AsyncClient(
            base_url="http://vision", transport=httpx.MockTransport(timeout)
        ) as http:
            with self.assertRaises(VisionTimeoutError):
                await HttpVisionDetector(http=http).detect(_image())

        def inference_failure(_: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"detail": "inference failed"})

        async with httpx.AsyncClient(
            base_url="http://vision", transport=httpx.MockTransport(inference_failure)
        ) as http:
            with self.assertRaises(VisionUnavailableError):
                await HttpVisionDetector(http=http).detect(_image())


def _image() -> ValidatedImage:
    return ValidatedImage(data=b"test-image-bytes", format=ImageFormat.JPEG, width=320, height=320)
