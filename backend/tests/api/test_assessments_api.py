"""HTTP-level tests: real FastAPI app, real middleware and handlers, fake ports behind the service."""

import unittest
from collections.abc import Iterator

from fastapi.testclient import TestClient

from app.adapters.db.memory_repository import InMemoryAssessmentRepository
from app.adapters.storage.memory import InMemoryImageStore
from app.core.config import Settings
from app.domain.errors import VisionUnavailableError
from app.domain.taxonomy import ECX_TAXONOMY
from app.main import create_app
from app.services.assessment_service import AssessmentService
from app.services.image_validation import ImageLimits
from tests.unit.fakes import CountingIds, FakeAdvisor, FakeVision, FixedClock, make_image, raw

BASE_ENV = {
    "vision_service_url": "http://vision.test",
    "gemini_api_key": "unused",
    "gemini_model": "unused",
    "image_store": "memory",
    "assessment_store": "memory",
}


def make_settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **{**BASE_ENV, **overrides})  # type: ignore[arg-type]


def make_client(
    *, vision: FakeVision | None = None, settings: Settings | None = None
) -> TestClient:
    settings = settings or make_settings()
    service = AssessmentService(
        vision=vision or FakeVision((raw("Full Black"), raw("Partial Black"))),
        advisor=FakeAdvisor(),
        images=InMemoryImageStore(),
        repository=InMemoryAssessmentRepository(),
        taxonomy=ECX_TAXONOMY,
        limits=ImageLimits(
            max_bytes=settings.max_image_bytes,
            max_pixels=settings.max_image_pixels,
            min_side_px=settings.min_image_side_px,
        ),
        clock=FixedClock(),
        new_id=CountingIds(),
        image_url_ttl_s=settings.image_url_ttl_s,
        retain_original_image=True,
    )
    return TestClient(create_app(settings=settings, service=service))


def upload(client: TestClient, data: bytes | None = None, **headers: str):  # noqa: ANN201
    return client.post(
        "/api/v1/assessments",
        files={"file": ("sample.jpg", data or make_image(), "image/jpeg")},
        headers=headers,
    )


class CreateAssessmentApiTests(unittest.TestCase):
    def test_created_response_has_the_documented_shape(self) -> None:
        client = make_client()
        response = upload(client)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers["Location"], "/api/v1/assessments/asmt_0001")
        self.assertIn("X-Request-ID", response.headers)
        body = response.json()
        self.assertEqual(body["status"], "completed")
        result = body["result"]
        self.assertEqual(result["summary"]["detection_count"], 2)
        self.assertEqual(result["summary"]["primary_detection_count"], 1)
        self.assertEqual(result["model_version"], "test-model-1")
        self.assertEqual(len(result["coverage"]["scanned"]), 3)
        self.assertEqual(len(result["coverage"]["not_scanned"]), 10)
        self.assertEqual(result["images"]["expires_in_s"], 900)
        self.assertIn("PRELIMINARY_AI_ASSESSMENT", [x["code"] for x in result["limitations"]])
        # Things this API must never claim:
        for forbidden in ("grade", "is_export_eligible", "cupping_notes", "healthy_beans_count"):
            self.assertNotIn(forbidden, body)
            self.assertNotIn(forbidden, result)

    def test_same_idempotency_key_replays_with_200(self) -> None:
        client = make_client()
        data = make_image()
        first = upload(client, data, **{"Idempotency-Key": "abc-1"})
        again = upload(client, data, **{"Idempotency-Key": "abc-1"})
        self.assertEqual((first.status_code, again.status_code), (201, 200))
        self.assertEqual(first.json()["assessment_id"], again.json()["assessment_id"])

    def test_same_key_with_another_image_is_409(self) -> None:
        client = make_client()
        upload(client, make_image(), **{"Idempotency-Key": "abc-1"})
        response = upload(client, make_image(), **{"Idempotency-Key": "abc-1"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "IDEMPOTENCY_KEY_REUSED")

    def test_malformed_idempotency_key_is_422(self) -> None:
        response = upload(make_client(), **{"Idempotency-Key": "has spaces!"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "INVALID_REQUEST")

    def test_not_an_image_is_400_with_the_error_envelope(self) -> None:
        response = upload(make_client(), b"hello")
        self.assertEqual(response.status_code, 400)
        error = response.json()["error"]
        self.assertEqual(error["code"], "INVALID_IMAGE")
        self.assertEqual(error["request_id"], response.headers["X-Request-ID"])
        self.assertIsNone(error["assessment_id"])

    def test_missing_file_is_422(self) -> None:
        response = make_client().post("/api/v1/assessments")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "INVALID_REQUEST")

    def test_vision_outage_is_502_and_recorded_as_failed(self) -> None:
        client = make_client(vision=FakeVision(error=VisionUnavailableError("down")))
        response = upload(client)
        self.assertEqual(response.status_code, 502)
        error = response.json()["error"]
        self.assertEqual(error["code"], "INFERENCE_FAILED")
        self.assertEqual(error["assessment_id"], "asmt_0001")
        self.assertNotIn("down", error["message"])  # internals stay in the logs

        failed = client.get(f"/api/v1/assessments/{error['assessment_id']}").json()
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["error_code"], "INFERENCE_FAILED")
        self.assertNotIn("result", failed)


class SizeLimitApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = make_settings(max_image_bytes=1_000)
        self.client = make_client(settings=self.settings)

    def test_declared_oversize_body_is_413_before_parsing(self) -> None:
        response = upload(self.client, b"x" * (self.settings.max_body_bytes + 10))
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["error"]["code"], "IMAGE_TOO_LARGE")

    def test_streamed_oversize_body_without_content_length_is_413(self) -> None:
        def chunks() -> Iterator[bytes]:
            for _ in range(3):
                yield b"x" * self.settings.max_body_bytes

        response = self.client.post(
            "/api/v1/assessments",
            content=chunks(),
            headers={"Content-Type": "multipart/form-data; boundary=x"},
        )
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["error"]["code"], "IMAGE_TOO_LARGE")

    def test_file_over_the_image_limit_but_under_the_body_limit_is_413(self) -> None:
        response = upload(self.client, b"x" * 5_000)
        self.assertEqual(response.status_code, 413)


class ReadApiTests(unittest.TestCase):
    def test_get_returns_the_same_assessment_with_fresh_urls(self) -> None:
        client = make_client()
        created = upload(client).json()
        fetched = client.get(f"/api/v1/assessments/{created['assessment_id']}")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json()["result"]["summary"], created["result"]["summary"])

    def test_unknown_id_is_404(self) -> None:
        response = make_client().get("/api/v1/assessments/asmt_nope")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "ASSESSMENT_NOT_FOUND")

    def test_listing_paginates_newest_first(self) -> None:
        client = make_client()
        for _ in range(3):
            upload(client)
        first = client.get("/api/v1/assessments", params={"limit": 2}).json()
        self.assertEqual([i["assessment_id"] for i in first["items"]], ["asmt_0003", "asmt_0002"])
        second = client.get(
            "/api/v1/assessments", params={"limit": 2, "cursor": first["next_cursor"]}
        ).json()
        self.assertEqual([i["assessment_id"] for i in second["items"]], ["asmt_0001"])
        self.assertIsNone(second["next_cursor"])

    def test_bad_cursor_and_bad_limit_are_422(self) -> None:
        client = make_client()
        self.assertEqual(client.get("/api/v1/assessments", params={"cursor": "junk"}).status_code, 422)
        self.assertEqual(client.get("/api/v1/assessments", params={"limit": 0}).status_code, 422)


class PlatformApiTests(unittest.TestCase):
    def test_health_is_minimal(self) -> None:
        body = make_client().get("/health").json()
        self.assertEqual(set(body), {"status", "version"})

    def test_removed_routes_are_gone(self) -> None:
        client = make_client()
        for method, path in (("post", "/api/v1/detect"), ("post", "/api/v1/reload-model")):
            with self.subTest(path=path):
                self.assertEqual(getattr(client, method)(path).status_code, 404)

    def test_unknown_route_uses_the_error_envelope(self) -> None:
        response = make_client().get("/nope")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json())

    def test_cors_allows_only_configured_origins(self) -> None:
        client = make_client(settings=make_settings(cors_allowed_origins="https://app.example"))
        allowed = client.options(
            "/api/v1/assessments",
            headers={"Origin": "https://app.example", "Access-Control-Request-Method": "POST"},
        )
        denied = client.options(
            "/api/v1/assessments",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
        )
        self.assertEqual(allowed.headers.get("access-control-allow-origin"), "https://app.example")
        self.assertNotIn("access-control-allow-origin", denied.headers)

    def test_openapi_documents_error_envelope_and_no_removed_fields(self) -> None:
        document = make_client().get("/openapi.json").json()
        self.assertIn("/api/v1/assessments", document["paths"])
        self.assertNotIn("/api/v1/detect", document["paths"])
        self.assertIn("ErrorResponse", document["components"]["schemas"])


if __name__ == "__main__":
    unittest.main()
