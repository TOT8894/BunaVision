"""End-to-end API tests with the vision and Gemini clients patched. Run with `python manage.py test`
(see README for the environment variables; SQLite is fine for tests)."""

import io
from unittest import mock

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APIClient, APITestCase
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts.models import User
from apps.assessments.clients import advisor, vision
from apps.assessments.clients.vision import RawDetection, VisionOutput
from apps.assessments.models import Assessment
from apps.common.errors import AdvisoryFailed, ModelReloadFailed, NotCoffeeImage, VisionUnavailable

PASSWORD = "a-long-enough-password"
ADVISORY = {
    "generator_model": "fake-gemini",
    "summary": {"en": "Summary.", "am": "ማጠቃለያ"},
    "recommendations": [{"en": "Sort the lot.", "am": "ቡናውን ይለዩ"}],
}


def jpeg(seed: int = 64, size: tuple[int, int] = (400, 400), fmt: str = "JPEG") -> bytes:
    buffer = io.BytesIO()
    Image.effect_noise(size, seed).convert("RGB").save(buffer, format=fmt)
    return buffer.getvalue()


def output(*labels: str) -> VisionOutput:
    return VisionOutput(
        model_version="test-model-1", validator_version="test-validator-1", coffee_confidence=0.97,
        detections=tuple(RawDetection(label, 0.9, (1.0, 2.0, 30.0, 40.0)) for label in labels),
        annotated_image=b"\xff\xd8\xff-annotated",
    )


class ApiTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()  # throttle counters live in the cache
        self.alice = self.client_for("alice@example.com")

    def client_for(self, email: str, *, staff: bool = False) -> APIClient:
        client = APIClient()
        User.objects.create_user(email, PASSWORD, is_staff=staff)
        token = client.post("/api/v1/auth/login", {"email": email, "password": PASSWORD}, format="json").json()["access_token"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    def upload(self, client: APIClient, data: bytes | None = None, **headers: str):  # noqa: ANN201
        file = SimpleUploadedFile("sample.jpg", data or jpeg(), content_type="image/jpeg")
        return client.post("/api/v1/assessments", {"image": file}, format="multipart", **headers)

    def run_pipeline(self, client: APIClient, vision_output: VisionOutput | None = None, data: bytes | None = None, **headers: str):  # noqa: ANN201
        detected = vision_output or output("Full Black", "Partial Black", "Partial Black")
        with mock.patch.object(vision, "detect", return_value=detected), mock.patch.object(advisor, "generate", return_value=ADVISORY):
            return self.upload(client, data, **headers)


class AuthTests(ApiTestCase):
    def test_register_login_me_and_identical_login_failures(self) -> None:
        anonymous = APIClient()
        created = anonymous.post("/api/v1/auth/register", {"email": " Bob@Example.com ", "password": PASSWORD}, format="json")
        self.assertEqual((created.status_code, created.json()["email"], created.json()["role"]), (201, "bob@example.com", "user"))
        self.assertEqual(anonymous.post("/api/v1/auth/register", {"email": "bob@example.com", "password": PASSWORD}, format="json").status_code, 409)

        wrong = anonymous.post("/api/v1/auth/login", {"email": "bob@example.com", "password": "wrong-password-1"}, format="json")
        unknown = anonymous.post("/api/v1/auth/login", {"email": "ghost@example.com", "password": PASSWORD}, format="json")
        self.assertEqual((wrong.status_code, unknown.status_code), (401, 401))
        self.assertEqual(wrong.json()["error"]["message"], unknown.json()["error"]["message"])
        self.assertEqual(self.alice.get("/api/v1/auth/me").json()["email"], "alice@example.com")

    def test_unauthenticated_requests_get_401_with_the_envelope(self) -> None:
        response = APIClient().get("/api/v1/assessments")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "AUTHENTICATION_REQUIRED")
        self.assertEqual(response["WWW-Authenticate"], "Bearer")
        self.assertIn("X-Request-ID", response)


class AssessmentTests(ApiTestCase):
    def test_successful_assessment_has_the_contract_shape(self) -> None:
        response = self.run_pipeline(self.alice)
        body = response.json()
        self.assertEqual((response.status_code, body["status"]), (201, "completed"))
        result = body["result"]
        self.assertEqual(
            (result["summary"]["detection_count"], result["summary"]["primary_detection_count"], result["summary"]["secondary_detection_count"]),
            (3, 1, 2),
        )
        self.assertTrue(result["image_check"]["is_coffee"])
        self.assertEqual(result["model_version"], "test-model-1")
        self.assertTrue(result["images"]["annotated_url"].startswith("http://memory.invalid/"))
        self.assertIn("PARTIAL_CLASS_COVERAGE", [x["code"] for x in result["limitations"]])
        self.assertEqual(result["advisory"]["generator_model"], "fake-gemini")

    def test_zero_detections_is_a_valid_result(self) -> None:
        body = self.run_pipeline(self.alice, output()).json()
        self.assertEqual((body["status"], body["result"]["summary"]["detection_count"], body["result"]["detections"]), ("completed", 0, []))

    def test_unknown_label_and_dependency_failures_are_recorded(self) -> None:
        ok = mock.Mock(return_value=output("Full Black"))
        cases = [
            ("unknown label", mock.Mock(return_value=output("Mystery Spot")), mock.Mock(return_value=ADVISORY), "INFERENCE_FAILED"),
            ("vision down", mock.Mock(side_effect=VisionUnavailable("down")), mock.Mock(return_value=ADVISORY), "INFERENCE_FAILED"),
            ("advisor down", ok, mock.Mock(side_effect=AdvisoryFailed("quota")), "ADVISORY_FAILED"),
        ]
        for name, detect, generate, code in cases:
            with self.subTest(name), mock.patch.object(vision, "detect", detect), mock.patch.object(advisor, "generate", generate):
                response = self.upload(self.alice)
            error = response.json()["error"]
            self.assertEqual((response.status_code, error["code"]), (502, code))
            recorded = Assessment.objects.get(id=error["assessment_id"])
            self.assertEqual((recorded.status, recorded.error_code, recorded.result), ("failed", code, None))
            shown = self.alice.get(f"/api/v1/assessments/{recorded.id}").json()
            self.assertEqual((shown["status"], shown["error_code"]), ("failed", code))

    def test_a_non_coffee_photo_is_rejected_and_not_recorded(self) -> None:
        rejection = NotCoffeeImage("gate", coffee_confidence=0.02, threshold=0.75)
        with mock.patch.object(vision, "detect", side_effect=rejection), mock.patch.object(advisor, "generate") as gemini:
            response = self.upload(self.alice)
        error = response.json()["error"]
        self.assertEqual((response.status_code, error["code"]), (422, "IMAGE_NOT_COFFEE"))
        self.assertEqual(error["details"], {"is_coffee": False, "coffee_confidence": 0.02, "threshold": 0.75})
        self.assertEqual(Assessment.objects.count(), 0)
        gemini.assert_not_called()

    def test_idempotent_replay_and_key_reuse_with_a_different_image(self) -> None:
        data = jpeg()
        first = self.run_pipeline(self.alice, data=data, HTTP_IDEMPOTENCY_KEY="k1")
        with mock.patch.object(vision, "detect") as detect:
            replay = self.upload(self.alice, data, HTTP_IDEMPOTENCY_KEY="k1")
            reuse = self.upload(self.alice, jpeg(seed=90), HTTP_IDEMPOTENCY_KEY="k1")
        self.assertEqual((first.status_code, replay.status_code), (201, 200))
        self.assertEqual(replay.json()["assessment_id"], first.json()["assessment_id"])
        self.assertEqual((reuse.status_code, reuse.json()["error"]["code"]), (422, "IDEMPOTENCY_KEY_REUSED"))
        detect.assert_not_called()  # a replay costs nothing

    def test_users_only_see_their_own_assessments(self) -> None:
        bob = self.client_for("bob@example.com")
        assessment_id = self.run_pipeline(self.alice).json()["assessment_id"]
        missing = bob.get(f"/api/v1/assessments/{assessment_id}")
        self.assertEqual((missing.status_code, missing.json()["error"]["code"]), (404, "ASSESSMENT_NOT_FOUND"))
        self.assertEqual(bob.get("/api/v1/assessments").json()["items"], [])

    def test_history_is_newest_first_and_cursor_paginated(self) -> None:
        ids = [self.run_pipeline(self.alice).json()["assessment_id"] for _ in range(3)]
        first = self.alice.get("/api/v1/assessments?limit=2").json()
        second = self.alice.get(f"/api/v1/assessments?limit=2&cursor={first['next_cursor']}").json()
        self.assertEqual([i["assessment_id"] for i in first["items"]], [ids[2], ids[1]])
        self.assertEqual(([i["assessment_id"] for i in second["items"]], second["next_cursor"]), ([ids[0]], None))

    def test_bad_uploads(self) -> None:
        cases = [
            (b"not an image", 400, "INVALID_IMAGE"),
            (jpeg(fmt="GIF"), 415, "UNSUPPORTED_FORMAT"),
        ]
        for data, status, code in cases:
            response = self.upload(self.alice, data=data)
            self.assertEqual((response.status_code, response.json()["error"]["code"]), (status, code))
        missing = self.alice.post("/api/v1/assessments", {}, format="multipart")
        self.assertEqual((missing.status_code, missing.json()["error"]["code"]), (422, "INVALID_REQUEST"))
        with override_settings(MAX_IMAGE_BYTES=100):
            too_big = self.upload(self.alice)
        self.assertEqual((too_big.status_code, too_big.json()["error"]["code"]), (413, "IMAGE_TOO_LARGE"))

    def test_hourly_quota_returns_429(self) -> None:
        rates = {"assessments": "2/hour", "auth": "1000/min"}
        with mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", rates):
            responses = [self.run_pipeline(self.alice) for _ in range(3)]
        self.assertEqual([r.status_code for r in responses], [201, 201, 429])
        self.assertEqual(responses[2].json()["error"]["code"], "RATE_LIMITED")
        self.assertIn("Retry-After", responses[2])


class AdminTests(ApiTestCase):
    ADMIN_GETS = ("/api/v1/admin/assessments", "/api/v1/admin/model-versions", "/api/v1/admin/overview", "/api/v1/admin/limits")

    def test_ordinary_users_are_forbidden_everywhere_in_the_admin_api(self) -> None:
        for path in self.ADMIN_GETS:
            self.assertEqual(self.alice.get(path).status_code, 403, path)
        self.assertEqual(self.alice.post("/api/v1/admin/vision/reload-model").status_code, 403)
        self.assertEqual(APIClient().get(self.ADMIN_GETS[0]).status_code, 401)

    def test_admin_sees_failures_versions_overview_limits_and_can_reload(self) -> None:
        self.run_pipeline(self.alice)
        with mock.patch.object(vision, "detect", side_effect=VisionUnavailable("down")):
            self.upload(self.alice, data=jpeg(seed=90))
        admin = self.client_for("root@example.com", staff=True)

        failed = admin.get("/api/v1/admin/assessments?status=failed").json()
        self.assertEqual([(i["status"], i["error_code"]) for i in failed["items"]], [("failed", "INFERENCE_FAILED")])
        self.assertEqual(admin.get("/api/v1/admin/assessments?status=nonsense").status_code, 422)
        detail = admin.get(f"/api/v1/admin/assessments/{failed['items'][0]['assessment_id']}").json()
        self.assertEqual(detail["owner_id"], str(User.objects.get(email="alice@example.com").pk))

        versions = admin.get("/api/v1/admin/model-versions").json()["versions"]
        self.assertEqual((versions[0]["model_version"], versions[0]["validator_version"], versions[0]["assessments"]), ("test-model-1", "test-validator-1", 1))
        outcomes = {(o["status"], o["error_code"]): o["count"] for o in admin.get("/api/v1/admin/overview").json()["outcomes"]}
        self.assertEqual(outcomes, {("completed", None): 1, ("failed", "INFERENCE_FAILED"): 1})
        self.assertIn("max_image_bytes", admin.get("/api/v1/admin/limits").json())

        with mock.patch.object(vision, "reload_model", return_value={"reloaded": True, "engine": "onnx"}):
            self.assertEqual(admin.post("/api/v1/admin/vision/reload-model").json(), {"reloaded": True, "engine": "onnx"})
        with mock.patch.object(vision, "reload_model", side_effect=ModelReloadFailed("boom")):
            failed_reload = admin.post("/api/v1/admin/vision/reload-model")
        self.assertEqual((failed_reload.status_code, failed_reload.json()["error"]["code"]), (502, "MODEL_RELOAD_FAILED"))
