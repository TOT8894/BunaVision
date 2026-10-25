"""Ports: what the workflow needs from the outside world, stated as interfaces.

The service layer depends on these Protocols and on nothing concrete. Adapters in
`app.adapters` implement them, so the vision service, Gemini, S3 and the database can each be
replaced or faked without touching business logic.

Types here are transport-free: no HTTP, no base64, no SDK objects.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.domain.models import (
    Advisory,
    Assessment,
    AssessmentPage,
    BoundingBox,
    Coverage,
    DetectionSummary,
)
from app.services.image_validation import ValidatedImage

# --- Vision ------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RawDetection:
    """One detection as the vision service reports it, before taxonomy mapping."""

    label: str
    confidence: float
    box: BoundingBox
    reported_category: str | None = None  # vision's own category text, for drift checks only


@dataclass(frozen=True, slots=True)
class VisionOutput:
    model_version: str
    detections: tuple[RawDetection, ...]
    annotated_image: bytes | None  # JPEG bytes, already decoded from the transport encoding


class VisionDetector(Protocol):
    async def detect(self, image: ValidatedImage) -> VisionOutput:
        """Localize supported defects. Raises `DependencyError` subclasses on failure."""
        ...


# --- Advisory ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AdvisoryFacts:
    """Everything the advisory writer is allowed to know. It never sees the image."""

    model_version: str
    summary: DetectionSummary
    coverage: Coverage


class AdvisoryGenerator(Protocol):
    async def generate(self, facts: AdvisoryFacts) -> Advisory:
        """Write the bilingual advisory. Raises `DependencyError` subclasses on failure."""
        ...


# --- Image storage -----------------------------------------------------------------------


class ImageStore(Protocol):
    async def put(self, key: str, data: bytes, content_type: str) -> None: ...

    async def url_for(self, key: str, ttl_s: int) -> str:
        """A time-limited URL for reading `key`. Never persist it."""
        ...

    async def delete(self, keys: Sequence[str]) -> None: ...


# --- Persistence -------------------------------------------------------------------------


class AssessmentRepository(Protocol):
    async def add(self, assessment: Assessment) -> None:
        """Store a new assessment.

        Raises `DuplicateIdempotencyKeyError` if (owner, idempotency_key) is already taken.
        """
        ...

    async def get(self, assessment_id: str, owner_id: str) -> Assessment | None:
        """Return the assessment only if `owner_id` owns it."""
        ...

    async def find_by_idempotency_key(self, owner_id: str, key: str) -> Assessment | None: ...

    async def list_for_owner(
        self, owner_id: str, *, limit: int, cursor: str | None
    ) -> AssessmentPage:
        """Newest first. Raises `InvalidRequestError` for a cursor it does not recognise."""
        ...


# --- Time --------------------------------------------------------------------------------


class Clock(Protocol):
    def now(self) -> datetime: ...

    def monotonic(self) -> float: ...
