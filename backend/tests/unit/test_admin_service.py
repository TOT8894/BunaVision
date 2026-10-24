import unittest
from datetime import timedelta

from app.adapters.db.memory_repository import InMemoryAssessmentRepository
from app.adapters.storage.memory import InMemoryImageStore
from app.domain.errors import (
    AssessmentNotFoundError,
    ErrorCode,
    InvalidRequestError,
    ModelReloadFailedError,
    VisionUnavailableError,
)
from app.domain.models import AssessmentStatus
from app.domain.operations import OperationalLimits
from app.domain.taxonomy import ECX_TAXONOMY
from app.services.admin_service import AdminService
from app.services.assessment_service import AssessmentService
from app.services.image_validation import ImageLimits
from tests.unit.fakes import (
    CountingIds,
    FakeAdvisor,
    FakeVision,
    FakeVisionAdmin,
    FixedClock,
    make_image,
    raw,
)

MIB = 1024 * 1024
LIMITS = OperationalLimits(
    max_image_bytes=10 * MIB, max_image_pixels=50_000_000, min_image_side_px=320,
    max_assessments_per_user_per_hour=30, max_concurrent_assessments=4,
    vision_timeout_s=30.0, gemini_timeout_s=30.0, image_url_ttl_s=900,
    retain_original_image=True,
)


class AdminTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.clock = FixedClock()
        self.repo = InMemoryAssessmentRepository()
        self.vision_admin = FakeVisionAdmin()
        self.admin = AdminService(
            queries=self.repo, vision_admin=self.vision_admin, limits=LIMITS, clock=self.clock
        )
        self.ids = CountingIds()

    def assessments_with(self, vision: FakeVision) -> AssessmentService:
        return AssessmentService(
            vision=vision, advisor=FakeAdvisor(), images=InMemoryImageStore(),
            repository=self.repo, taxonomy=ECX_TAXONOMY,
            limits=ImageLimits(10 * MIB, 50_000_000, 320), clock=self.clock, new_id=self.ids,
            image_url_ttl_s=900, retain_original_image=True,
            max_assessments_per_hour=1000, max_concurrent_assessments=8,
        )

    async def seed(self) -> None:
        good = self.assessments_with(FakeVision((raw("Full Black"), raw("Partial Black"))))
        await good.create_assessment(data=make_image(), owner_id="alice")
        await good.create_assessment(data=make_image(), owner_id="bob")
        broken = self.assessments_with(FakeVision(error=VisionUnavailableError("down")))
        for owner in ("alice", "bob"):
            with self.assertRaises(VisionUnavailableError):
                await broken.create_assessment(data=make_image(), owner_id=owner)


class ProcessingFailureTests(AdminTestCase):
    async def test_admin_sees_failures_from_every_user_with_their_error_codes(self) -> None:
        await self.seed()
        page = await self.admin.list_assessments(
            status=AssessmentStatus.FAILED, error_code=None, owner_id=None, limit=10, cursor=None
        )
        self.assertEqual({a.owner_id for a in page.items}, {"alice", "bob"})
        self.assertTrue(all(a.error_code is ErrorCode.INFERENCE_FAILED for a in page.items))

    async def test_filters_combine_and_paginate(self) -> None:
        await self.seed()
        only_alice = await self.admin.list_assessments(
            status=AssessmentStatus.FAILED, error_code=ErrorCode.INFERENCE_FAILED,
            owner_id="alice", limit=10, cursor=None,
        )
        self.assertEqual([a.owner_id for a in only_alice.items], ["alice"])

        first = await self.admin.list_assessments(status=None, error_code=None, owner_id=None, limit=3, cursor=None)
        second = await self.admin.list_assessments(
            status=None, error_code=None, owner_id=None, limit=3, cursor=first.next_cursor
        )
        self.assertEqual((len(first.items), len(second.items), second.next_cursor), (3, 1, None))

    async def test_bad_cursor_is_a_client_error(self) -> None:
        with self.assertRaises(InvalidRequestError):
            await self.admin.list_assessments(
                status=None, error_code=None, owner_id=None, limit=5, cursor="garbage"
            )

    async def test_can_open_any_users_record_but_unknown_ids_are_404(self) -> None:
        await self.seed()
        self.assertEqual((await self.admin.get_assessment("asmt_0001")).owner_id, "alice")
        with self.assertRaises(AssessmentNotFoundError):
            await self.admin.get_assessment("asmt_9999")

    async def test_overview_counts_outcomes_inside_the_window_only(self) -> None:
        await self.seed()
        overview = await self.admin.outcome_overview(window_hours=24)
        counts = {(o.status, o.error_code): o.count for o in overview.outcomes}
        self.assertEqual(counts[(AssessmentStatus.COMPLETED, None)], 2)
        self.assertEqual(counts[(AssessmentStatus.FAILED, ErrorCode.INFERENCE_FAILED)], 2)

        self.clock._now += timedelta(hours=48)  # everything is now older than the window
        self.assertEqual((await self.admin.outcome_overview(window_hours=24)).outcomes, ())


class ModelVersionTests(AdminTestCase):
    async def test_usage_is_grouped_by_model_and_validator_version(self) -> None:
        await self.seed()
        usage = await self.admin.model_version_usage()
        self.assertEqual(len(usage), 1)  # failures carry no model version, so they are excluded
        self.assertEqual(
            (usage[0].model_version, usage[0].validator_version, usage[0].assessments),
            ("test-model-1", "test-validator-1", 2),
        )
        self.assertLess(usage[0].first_seen, usage[0].last_seen)

    async def test_no_usage_before_any_completed_assessment(self) -> None:
        self.assertEqual(await self.admin.model_version_usage(), ())


class LimitsAndReloadTests(AdminTestCase):
    def test_limits_are_reported_as_configured(self) -> None:
        self.assertEqual(self.admin.operational_limits(), LIMITS)

    async def test_reload_goes_through_the_vision_admin_port(self) -> None:
        result = await self.admin.reload_vision_model(actor_id="admin-1")
        self.assertEqual((result.reloaded, result.engine), (True, "onnx"))
        self.assertEqual(self.vision_admin.reloads, 1)

    async def test_failed_reload_is_reported_not_swallowed(self) -> None:
        admin = AdminService(
            queries=self.repo, vision_admin=FakeVisionAdmin(error=ModelReloadFailedError("boom")),
            limits=LIMITS, clock=self.clock,
        )
        with self.assertRaises(ModelReloadFailedError):
            await admin.reload_vision_model(actor_id="admin-1")


if __name__ == "__main__":
    unittest.main()
