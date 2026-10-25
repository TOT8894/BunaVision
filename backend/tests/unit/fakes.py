"""Hand-written fakes for the service ports. Real in-memory adapters stand in for storage."""

import io
from datetime import UTC, datetime, timedelta

from PIL import Image

from app.domain.errors import BunaVisionError, PersistenceError
from app.domain.models import (
    Advisory,
    Assessment,
    AssessmentPage,
    BilingualText,
    BoundingBox,
    ImageCheck,
)
from app.services.image_validation import ValidatedImage
from app.services.ports import AdvisoryFacts, RawDetection, VisionOutput


def make_image(fmt: str = "JPEG", size: tuple[int, int] = (400, 400), seed: int = 64) -> bytes:
    """A valid noisy image; `seed` changes the bytes so two images are never identical."""
    image = Image.effect_noise(size, seed).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


def raw(label: str, confidence: float = 0.9) -> RawDetection:
    return RawDetection(label=label, confidence=confidence, box=BoundingBox(1.0, 2.0, 30.0, 40.0))


class FakeVision:
    def __init__(
        self, detections: tuple[RawDetection, ...] = (), *, error: BunaVisionError | None = None,
        annotated: bytes | None = b"\xff\xd8\xff-annotated",
    ) -> None:
        self._detections = detections
        self.error = error
        self._annotated = annotated
        self.calls = 0

    async def detect(self, image: ValidatedImage) -> VisionOutput:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return VisionOutput(
            model_version="test-model-1",
            image_check=ImageCheck(coffee_confidence=0.97, validator_version="test-validator-1"),
            detections=self._detections,
            annotated_image=self._annotated,
        )


class FakeAdvisor:
    def __init__(self, *, error: BunaVisionError | None = None) -> None:
        self._error = error
        self.seen: list[AdvisoryFacts] = []

    async def generate(self, facts: AdvisoryFacts) -> Advisory:
        self.seen.append(facts)
        if self._error is not None:
            raise self._error
        return Advisory(
            generator_model="fake-gemini",
            summary=BilingualText(en="Summary.", am="ማጠቃለያ"),
            recommendations=(BilingualText(en="Sort the lot.", am="ቡናውን ይለዩ"),),
        )


class FixedClock:
    """Each `now()` call advances one second so assessments sort deterministically."""

    def __init__(self) -> None:
        self._now = datetime(2026, 10, 21, 8, 0, 0, tzinfo=UTC)
        self._mono = 100.0

    def now(self) -> datetime:
        self._now += timedelta(seconds=1)
        return self._now

    def monotonic(self) -> float:
        self._mono += 0.25
        return self._mono


class CountingIds:
    def __init__(self) -> None:
        self._n = 0

    def __call__(self) -> str:
        self._n += 1
        return f"asmt_{self._n:04d}"


class FlakyRepository:
    """Wraps a real repository; fails the first `fail_adds` calls to `add`."""

    def __init__(self, inner, *, fail_adds: int) -> None:  # noqa: ANN001
        self._inner = inner
        self._remaining = fail_adds

    async def add(self, assessment: Assessment) -> None:
        if self._remaining > 0:
            self._remaining -= 1
            raise PersistenceError("simulated database outage")
        await self._inner.add(assessment)

    async def get(self, assessment_id: str, owner_id: str) -> Assessment | None:
        return await self._inner.get(assessment_id, owner_id)

    async def find_by_idempotency_key(self, owner_id: str, key: str) -> Assessment | None:
        return await self._inner.find_by_idempotency_key(owner_id, key)

    async def list_for_owner(
        self, owner_id: str, *, limit: int, cursor: str | None
    ) -> AssessmentPage:
        return await self._inner.list_for_owner(owner_id, limit=limit, cursor=cursor)

    async def count_since(self, owner_id: str, since: datetime) -> int:
        return await self._inner.count_since(owner_id, since)


class RacyRepository:
    """Simulates two same-key requests racing: our pre-check misses, our `add` loses."""

    def __init__(self, inner, winner: Assessment) -> None:  # noqa: ANN001
        self._inner = inner
        self._winner = winner
        self._first_lookup = True

    async def add(self, assessment: Assessment) -> None:
        await self._inner.add(self._winner)  # the other request committed first
        await self._inner.add(assessment)  # raises DuplicateIdempotencyKeyError

    async def get(self, assessment_id: str, owner_id: str) -> Assessment | None:
        return await self._inner.get(assessment_id, owner_id)

    async def find_by_idempotency_key(self, owner_id: str, key: str) -> Assessment | None:
        if self._first_lookup:
            self._first_lookup = False
            return None
        return await self._inner.find_by_idempotency_key(owner_id, key)

    async def list_for_owner(
        self, owner_id: str, *, limit: int, cursor: str | None
    ) -> AssessmentPage:
        return await self._inner.list_for_owner(owner_id, limit=limit, cursor=cursor)

    async def count_since(self, owner_id: str, since: datetime) -> int:
        return await self._inner.count_since(owner_id, since)


class FakeVisionAdmin:
    def __init__(self, *, error: BunaVisionError | None = None) -> None:
        self._error = error
        self.reloads = 0

    async def reload_model(self):  # noqa: ANN201
        from app.domain.operations import ModelReloadResult

        self.reloads += 1
        if self._error is not None:
            raise self._error
        return ModelReloadResult(reloaded=True, engine="onnx")
