"""Hand-written fakes for the service ports. No mocking library needed."""

import io
from datetime import UTC, datetime

from PIL import Image

from app.domain.errors import BunaVisionError, DuplicateIdempotencyKeyError, PersistenceError
from app.domain.models import (
    Advisory,
    Assessment,
    AssessmentPage,
    BilingualText,
    BoundingBox,
)
from app.services.image_validation import ValidatedImage
from app.services.ports import AdvisoryFacts, RawDetection, VisionOutput

BOX = BoundingBox(10, 10, 50, 50)
JPEG_BYTES = b"\xff\xd8\xff\xe0fake-annotated-jpeg"


def make_image(seed: int = 64, size: tuple[int, int] = (400, 400), fmt: str = "JPEG") -> bytes:
    image = Image.effect_noise(size, seed).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


def raw(label: str, confidence: float = 0.9, category: str | None = None) -> RawDetection:
    return RawDetection(label=label, confidence=confidence, box=BOX, reported_category=category)


class FixedClock:
    """Wall clock frozen; monotonic advances 5 ms per read so durations are non-zero."""

    def __init__(self) -> None:
        self._ticks = 0

    def now(self) -> datetime:
        return datetime(2026, 10, 21, 8, 0, tzinfo=UTC)

    def monotonic(self) -> float:
        self._ticks += 1
        return self._ticks * 0.005


class CountingIds:
    def __init__(self) -> None:
        self._n = 0

    def __call__(self) -> str:
        self._n += 1
        return f"asmt_{self._n:04d}"


class FakeVision:
    def __init__(
        self,
        detections: tuple[RawDetection, ...] = (),
        *,
        error: BunaVisionError | None = None,
        annotated: bytes | None = JPEG_BYTES,
        model_version: str = "test-model-1",
    ) -> None:
        self._detections = detections
        self.error = error
        self._annotated = annotated
        self._model_version = model_version
        self.calls = 0

    async def detect(self, image: ValidatedImage) -> VisionOutput:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return VisionOutput(
            model_version=self._model_version,
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
            summary=BilingualText(en="Summary.", am="ማጠቃለያ።"),
            recommendations=(BilingualText(en="Verify manually.", am="በእጅ ያረጋግጡ።"),),
        )


class FlakyRepository:
    """Wraps a real repository; the first `fail_adds` calls to `add` raise PersistenceError."""

    def __init__(self, inner: object, *, fail_adds: int) -> None:
        self._inner = inner
        self._remaining = fail_adds

    async def add(self, assessment: Assessment) -> None:
        if self._remaining > 0:
            self._remaining -= 1
            raise PersistenceError("simulated database outage")
        await self._inner.add(assessment)  # type: ignore[attr-defined]

    async def get(self, assessment_id: str, owner_id: str) -> Assessment | None:
        return await self._inner.get(assessment_id, owner_id)  # type: ignore[attr-defined,no-any-return]

    async def find_by_idempotency_key(self, owner_id: str, key: str) -> Assessment | None:
        return await self._inner.find_by_idempotency_key(owner_id, key)  # type: ignore[attr-defined,no-any-return]

    async def list_for_owner(
        self, owner_id: str, *, limit: int, cursor: str | None
    ) -> AssessmentPage:
        return await self._inner.list_for_owner(owner_id, limit=limit, cursor=cursor)  # type: ignore[attr-defined,no-any-return]


class RacyRepository(FlakyRepository):
    """Simulates losing an idempotency race: the key looks free, then `add` reports a duplicate.

    After the failed `add`, lookups return the winner, as a real database would.
    """

    def __init__(self, inner: object, winner: Assessment) -> None:
        super().__init__(inner, fail_adds=0)
        self._winner = winner
        self._lost = False

    async def add(self, assessment: Assessment) -> None:
        self._lost = True
        raise DuplicateIdempotencyKeyError("lost the race")

    async def find_by_idempotency_key(self, owner_id: str, key: str) -> Assessment | None:
        return self._winner if self._lost else None
