import asyncio
import hashlib
import unittest
from collections.abc import Callable
from typing import Any

from app.adapters.db.memory_repository import InMemoryAssessmentRepository
from app.adapters.storage.memory import InMemoryImageStore
from app.domain.errors import (
    AdvisoryUnavailableError,
    AssessmentNotFoundError,
    ErrorCode,
    IdempotencyKeyReusedError,
    InvalidImageError,
    InvalidRequestError,
    NotCoffeeImageError,
    PersistenceError,
    RateLimitedError,
    UnknownDefectClassError,
    VisionTimeoutError,
    VisionUnavailableError,
)
from app.domain.models import AssessmentStatus
from app.domain.taxonomy import ECX_TAXONOMY
from app.services.assessment_service import AssessmentService
from app.services.image_validation import ImageLimits
from tests.unit.fakes import (
    CountingIds,
    FakeAdvisor,
    FakeVision,
    FixedClock,
    FlakyRepository,
    RacyRepository,
    make_image,
    raw,
)

MIB = 1024 * 1024
OWNER = "owner"
THREE = (raw("Full Black"), raw("Partial Black"), raw("Partial Black", 0.5))


class ServiceTestCase(unittest.IsolatedAsyncioTestCase):
    def build(
        self,
        *,
        vision: FakeVision | None = None,
        advisor: FakeAdvisor | None = None,
        retain: bool = True,
        wrap_repo: Callable[[Any], Any] | None = None,
        per_hour: int = 1000,
        concurrent: int = 8,
    ) -> AssessmentService:
        self.images = InMemoryImageStore()
        self.repo = InMemoryAssessmentRepository()
        self.vision = vision or FakeVision(THREE)
        self.advisor = advisor or FakeAdvisor()
        return AssessmentService(
            vision=self.vision,
            advisor=self.advisor,
            images=self.images,
            repository=wrap_repo(self.repo) if wrap_repo else self.repo,
            taxonomy=ECX_TAXONOMY,
            limits=ImageLimits(max_bytes=10 * MIB, max_pixels=50_000_000, min_side_px=320),
            clock=FixedClock(),
            new_id=CountingIds(),
            image_url_ttl_s=900,
            retain_original_image=retain,
            max_assessments_per_hour=per_hour,
            max_concurrent_assessments=concurrent,
        )


class CreateAssessmentTests(ServiceTestCase):
    async def test_completed_assessment_maps_detections_and_stores_images(self) -> None:
        service = self.build()
        outcome = await service.create_assessment(data=make_image(), owner_id=OWNER)

        assessment = outcome.view.assessment
        self.assertTrue(outcome.created)
        self.assertIs(assessment.status, AssessmentStatus.COMPLETED)
        result = assessment.result
        assert result is not None
        self.assertEqual(result.model_version, "test-model-1")
        self.assertEqual(
            (result.summary.detection_count, result.summary.primary_count, result.summary.secondary_count),
            (3, 1, 2),
        )
        self.assertEqual(self.images.keys(), {result.original_image_key, result.annotated_image_key})
        self.assertTrue(outcome.view.original_image_url.startswith("memory://"))  # type: ignore[union-attr]
        self.assertEqual(self.advisor.seen[0].summary.detection_count, 3)

    async def test_zero_detections_is_a_valid_completed_result(self) -> None:
        service = self.build(vision=FakeVision(()))
        outcome = await service.create_assessment(data=make_image(), owner_id=OWNER)
        result = outcome.view.assessment.result
        assert result is not None
        self.assertIs(outcome.view.assessment.status, AssessmentStatus.COMPLETED)
        self.assertEqual(result.summary.detection_count, 0)
        self.assertEqual(result.summary.by_class, ())

    async def test_original_image_is_not_kept_when_retention_is_off(self) -> None:
        service = self.build(retain=False)
        outcome = await service.create_assessment(data=make_image(), owner_id=OWNER)
        result = outcome.view.assessment.result
        assert result is not None
        self.assertIsNone(result.original_image_key)
        self.assertIsNone(outcome.view.original_image_url)
        self.assertEqual(self.images.keys(), {result.annotated_image_key})

    async def test_missing_annotated_image_is_allowed(self) -> None:
        service = self.build(vision=FakeVision(THREE, annotated=None))
        outcome = await service.create_assessment(data=make_image(), owner_id=OWNER)
        self.assertIsNone(outcome.view.annotated_image_url)


class CoffeeGateTests(ServiceTestCase):
    async def test_a_passing_check_is_kept_with_the_result(self) -> None:
        service = self.build()
        outcome = await service.create_assessment(data=make_image(), owner_id=OWNER)
        result = outcome.view.assessment.result
        assert result is not None
        self.assertEqual(result.image_check.validator_version, "test-validator-1")
        self.assertAlmostEqual(result.image_check.coffee_confidence, 0.97)

    async def test_a_non_coffee_photo_is_rejected_and_not_recorded(self) -> None:
        rejection = NotCoffeeImageError("gate", coffee_confidence=0.02, threshold=0.75)
        service = self.build(vision=FakeVision(error=rejection))
        with self.assertRaises(NotCoffeeImageError) as caught:
            await service.create_assessment(data=make_image(), owner_id=OWNER)
        self.assertEqual(
            caught.exception.public_details,
            {"is_coffee": False, "coffee_confidence": 0.02, "threshold": 0.75},
        )
        page = await self.repo.list_for_owner(OWNER, limit=10, cursor=None)
        self.assertEqual(page.items, ())  # a wrong photo is not a processing failure
        self.assertEqual(self.images.keys(), set())
        self.assertEqual(self.advisor.seen, [])  # no Gemini spend on a rejected photo


class LimitTests(ServiceTestCase):
    async def test_hourly_quota_blocks_the_next_assessment_but_not_replays(self) -> None:
        service = self.build(per_hour=2)
        data = make_image()
        await service.create_assessment(data=data, owner_id=OWNER, idempotency_key="k1")
        await service.create_assessment(data=make_image(seed=90), owner_id=OWNER)

        with self.assertRaises(RateLimitedError):
            await service.create_assessment(data=make_image(seed=40), owner_id=OWNER)
        replay = await service.create_assessment(data=data, owner_id=OWNER, idempotency_key="k1")
        self.assertFalse(replay.created)  # a replay costs nothing, so it is still allowed
        other = await service.create_assessment(data=make_image(), owner_id="someone-else")
        self.assertTrue(other.created)  # quotas are per user

    async def test_failed_attempts_count_towards_the_quota(self) -> None:
        service = self.build(vision=FakeVision(error=VisionUnavailableError("down")), per_hour=1)
        with self.assertRaises(VisionUnavailableError):
            await service.create_assessment(data=make_image(), owner_id=OWNER)
        with self.assertRaises(RateLimitedError):
            await service.create_assessment(data=make_image(), owner_id=OWNER)

    async def test_busy_service_rejects_instead_of_queueing(self) -> None:
        gate = asyncio.Event()

        class BlockingVision(FakeVision):
            async def detect(self, image):  # noqa: ANN001, ANN202
                await gate.wait()
                return await super().detect(image)

        service = self.build(vision=BlockingVision(THREE), concurrent=1)
        first = asyncio.create_task(service.create_assessment(data=make_image(), owner_id=OWNER))
        await asyncio.sleep(0)  # let the first request take the only slot
        with self.assertRaises(RateLimitedError):
            await service.create_assessment(data=make_image(seed=90), owner_id=OWNER)
        gate.set()
        self.assertTrue((await first).created)
        # the slot is free again afterwards
        again = await service.create_assessment(data=make_image(seed=40), owner_id=OWNER)
        self.assertTrue(again.created)


class FailureTests(ServiceTestCase):
    async def assert_failed_and_recorded(self, code: ErrorCode, assessment_id: str = "asmt_0001") -> None:
        record = await self.repo.get(assessment_id, OWNER)
        assert record is not None
        self.assertIs(record.status, AssessmentStatus.FAILED)
        self.assertIs(record.error_code, code)
        self.assertIsNone(record.result)

    async def test_unknown_defect_label_fails_loudly_and_is_recorded(self) -> None:
        service = self.build(vision=FakeVision((raw("Mystery Spot"),)))
        with self.assertRaises(UnknownDefectClassError) as caught:
            await service.create_assessment(data=make_image(), owner_id=OWNER)
        self.assertEqual(caught.exception.assessment_id, "asmt_0001")
        await self.assert_failed_and_recorded(ErrorCode.INFERENCE_FAILED)
        self.assertEqual(self.images.keys(), set())
        self.assertEqual(self.advisor.seen, [])

    async def test_vision_outage_and_timeout_keep_distinct_codes(self) -> None:
        for error, code in (
            (VisionUnavailableError("down"), ErrorCode.INFERENCE_FAILED),
            (VisionTimeoutError("slow"), ErrorCode.INFERENCE_TIMEOUT),
        ):
            with self.subTest(code=code):
                service = self.build(vision=FakeVision(error=error))
                with self.assertRaises(type(error)):
                    await service.create_assessment(data=make_image(), owner_id=OWNER)
                await self.assert_failed_and_recorded(code)
                self.assertEqual(self.images.keys(), set())

    async def test_advisory_failure_is_recorded_and_leaves_no_images(self) -> None:
        service = self.build(advisor=FakeAdvisor(error=AdvisoryUnavailableError("quota")))
        with self.assertRaises(AdvisoryUnavailableError):
            await service.create_assessment(data=make_image(), owner_id=OWNER)
        await self.assert_failed_and_recorded(ErrorCode.ADVISORY_FAILED)
        self.assertEqual(self.images.keys(), set())

    async def test_failed_save_discards_images_and_records_the_failure(self) -> None:
        service = self.build(wrap_repo=lambda inner: FlakyRepository(inner, fail_adds=1))
        with self.assertRaises(PersistenceError):
            await service.create_assessment(data=make_image(), owner_id=OWNER)
        self.assertEqual(self.images.keys(), set())
        await self.assert_failed_and_recorded(ErrorCode.PERSISTENCE_FAILED)

    async def test_invalid_image_is_rejected_without_a_record_or_vision_call(self) -> None:
        service = self.build()
        with self.assertRaises(InvalidImageError):
            await service.create_assessment(data=b"not an image", owner_id=OWNER)
        self.assertEqual(self.vision.calls, 0)
        page = await self.repo.list_for_owner(OWNER, limit=10, cursor=None)
        self.assertEqual(page.items, ())


class IdempotencyTests(ServiceTestCase):
    async def test_retry_with_same_key_and_image_returns_the_first_result(self) -> None:
        service = self.build()
        data = make_image()
        first = await service.create_assessment(data=data, owner_id=OWNER, idempotency_key="k1")
        again = await service.create_assessment(data=data, owner_id=OWNER, idempotency_key="k1")

        self.assertTrue(first.created)
        self.assertFalse(again.created)
        self.assertEqual(first.view.assessment.assessment_id, again.view.assessment.assessment_id)
        self.assertEqual(self.vision.calls, 1)
        self.assertEqual(len(self.images.keys()), 2)

    async def test_same_key_with_a_different_image_is_rejected(self) -> None:
        service = self.build()
        await service.create_assessment(data=make_image(seed=64), owner_id=OWNER, idempotency_key="k1")
        with self.assertRaises(IdempotencyKeyReusedError):
            await service.create_assessment(data=make_image(seed=90), owner_id=OWNER, idempotency_key="k1")
        self.assertEqual(self.vision.calls, 1)

    async def test_keys_are_scoped_per_owner(self) -> None:
        service = self.build()
        data = make_image()
        a = await service.create_assessment(data=data, owner_id="alice", idempotency_key="k")
        b = await service.create_assessment(data=data, owner_id="bob", idempotency_key="k")
        self.assertTrue(a.created and b.created)
        self.assertNotEqual(a.view.assessment.assessment_id, b.view.assessment.assessment_id)

    async def test_a_failed_attempt_does_not_hold_the_key(self) -> None:
        service = self.build(vision=FakeVision(THREE, error=VisionUnavailableError("down")))
        data = make_image()
        with self.assertRaises(VisionUnavailableError):
            await service.create_assessment(data=data, owner_id=OWNER, idempotency_key="k")
        self.vision.error = None  # the dependency recovers
        retry = await service.create_assessment(data=data, owner_id=OWNER, idempotency_key="k")
        self.assertTrue(retry.created)

    async def test_losing_a_race_replays_the_winner_and_cleans_up(self) -> None:
        data = make_image()
        scratch = self.build()
        winner = (await scratch.create_assessment(data=data, owner_id=OWNER, idempotency_key="k")).view.assessment

        service = self.build(wrap_repo=lambda inner: RacyRepository(inner, winner))
        outcome = await service.create_assessment(data=data, owner_id=OWNER, idempotency_key="k")

        self.assertFalse(outcome.created)
        self.assertEqual(outcome.view.assessment.assessment_id, winner.assessment_id)
        self.assertEqual(self.images.keys(), set())  # the loser's images were discarded
        self.assertEqual(winner.image_sha256, hashlib.sha256(data).hexdigest())


class ReadTests(ServiceTestCase):
    async def test_another_owner_cannot_read_an_assessment(self) -> None:
        service = self.build()
        outcome = await service.create_assessment(data=make_image(), owner_id="alice")
        assessment_id = outcome.view.assessment.assessment_id
        view = await service.get_assessment(assessment_id=assessment_id, owner_id="alice")
        self.assertIsNotNone(view.annotated_image_url)
        with self.assertRaises(AssessmentNotFoundError):
            await service.get_assessment(assessment_id=assessment_id, owner_id="bob")

    async def test_listing_is_newest_first_and_cursor_paginated(self) -> None:
        service = self.build()
        for _ in range(5):
            await service.create_assessment(data=make_image(), owner_id=OWNER)

        first = await service.list_assessments(owner_id=OWNER, limit=2, cursor=None)
        second = await service.list_assessments(owner_id=OWNER, limit=2, cursor=first.next_cursor)
        third = await service.list_assessments(owner_id=OWNER, limit=2, cursor=second.next_cursor)

        ids = [a.assessment_id for page in (first, second, third) for a in page.items]
        self.assertEqual(ids, ["asmt_0005", "asmt_0004", "asmt_0003", "asmt_0002", "asmt_0001"])
        self.assertIsNone(third.next_cursor)

    async def test_unrecognised_cursor_is_a_client_error(self) -> None:
        service = self.build()
        with self.assertRaises(InvalidRequestError):
            await service.list_assessments(owner_id=OWNER, limit=5, cursor="garbage")


if __name__ == "__main__":
    unittest.main()
