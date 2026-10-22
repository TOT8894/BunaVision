import base64
import json
import unittest

import httpx

from app.adapters.vision_client.client import HttpVisionDetector
from app.domain.errors import (
    VisionBadResponseError,
    VisionTimeoutError,
    VisionUnavailableError,
)
from app.services.image_validation import ImageFormat, ValidatedImage

JPEG = b"\xff\xd8\xff\xe0annotated"
IMAGE = ValidatedImage(data=b"bytes", format=ImageFormat.JPEG, width=400, height=400)


def detection(label: str = "Full Black", category: str = "Primary Defect") -> dict:
    return {
        "box": {"x1": 1, "y1": 2, "x2": 30, "y2": 40},
        "class_name": label,
        "confidence": 0.8,
        "category": category,
    }


def body(detections: list[dict], **extra: object) -> dict:
    return {
        "model_version": "v-test",
        "total_beans": len(detections),
        "healthy_beans": -1,
        "defect_beans": len(detections),
        "defect_counts": {},
        "detected_beans": detections,
        "annotated_image_base64": base64.b64encode(JPEG).decode(),
        **extra,
    }


def detector(handler: httpx.MockTransport | None = None, *, fn=None) -> HttpVisionDetector:
    transport = handler or httpx.MockTransport(fn)
    return HttpVisionDetector(
        http=httpx.AsyncClient(base_url="http://vision.test", transport=transport)
    )


class VisionClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_maps_detections_and_decodes_the_annotated_image(self) -> None:
        seen: dict[str, object] = {}

        def fn(request: httpx.Request) -> httpx.Response:
            seen["path"] = request.url.path
            seen["has_file_field"] = b'name="file"' in request.content
            seen["no_user_filename"] = b"upload.jpg" in request.content
            return httpx.Response(200, json=body([detection(), detection("Partial Black", "Secondary Defect")]))

        output = await detector(fn=fn).detect(IMAGE)

        self.assertEqual(seen, {"path": "/detect", "has_file_field": True, "no_user_filename": True})
        self.assertEqual(output.model_version, "v-test")
        self.assertEqual([d.label for d in output.detections], ["Full Black", "Partial Black"])
        self.assertEqual(output.detections[0].reported_category, "Primary Defect")
        self.assertEqual(output.annotated_image, JPEG)

    async def test_zero_detections_is_a_valid_result(self) -> None:
        output = await detector(fn=lambda r: httpx.Response(200, json=body([]))).detect(IMAGE)
        self.assertEqual(output.detections, ())

    async def test_missing_annotated_image_is_allowed(self) -> None:
        payload = body([detection()], annotated_image_base64=None)
        output = await detector(fn=lambda r: httpx.Response(200, json=payload)).detect(IMAGE)
        self.assertIsNone(output.annotated_image)

    async def test_missing_detection_list_is_a_broken_contract_not_zero_detections(self) -> None:
        payload = body([])
        del payload["detected_beans"]
        with self.assertRaises(VisionBadResponseError):
            await detector(fn=lambda r: httpx.Response(200, json=payload)).detect(IMAGE)

    async def test_count_that_disagrees_with_the_list_is_rejected(self) -> None:
        payload = body([detection()], defect_beans=5)
        with self.assertRaises(VisionBadResponseError):
            await detector(fn=lambda r: httpx.Response(200, json=payload)).detect(IMAGE)

    async def test_malformed_content_is_rejected(self) -> None:
        cases = {
            "not json": httpx.Response(200, content=b"<html>"),
            "bad box": httpx.Response(200, json=body([{**detection(), "box": {"x1": 9, "y1": 9, "x2": 1, "y2": 1}}])),
            "confidence out of range": httpx.Response(200, json=body([{**detection(), "confidence": 1.5}])),
            "bad base64": httpx.Response(200, json=body([], annotated_image_base64="***")),
            "not a jpeg": httpx.Response(200, json=body([], annotated_image_base64=base64.b64encode(b"PNG...").decode())),
        }
        for name, response in cases.items():
            with self.subTest(name), self.assertRaises(VisionBadResponseError):
                await detector(fn=lambda r, resp=response: resp).detect(IMAGE)

    async def test_status_codes_map_to_distinct_errors(self) -> None:
        for status, expected in ((500, VisionUnavailableError), (503, VisionUnavailableError),
                                 (429, VisionUnavailableError), (422, VisionBadResponseError),
                                 (404, VisionBadResponseError)):
            with self.subTest(status=status), self.assertRaises(expected):
                await detector(fn=lambda r, s=status: httpx.Response(s, text="x")).detect(IMAGE)

    async def test_timeout_and_connection_failure_are_distinguished(self) -> None:
        def slow(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("slow", request=request)

        def down(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused", request=request)

        with self.assertRaises(VisionTimeoutError):
            await detector(fn=slow).detect(IMAGE)
        with self.assertRaises(VisionUnavailableError):
            await detector(fn=down).detect(IMAGE)


if __name__ == "__main__":
    unittest.main()
