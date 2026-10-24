"""Domain entities.

Plain frozen dataclasses: no Pydantic, no FastAPI, no AWS. The public API models live in
`app.schemas`; these are what the workflow reasons about and what repositories store.

What is deliberately NOT here: total bean count, healthy bean count, defect percentage, grade,
export eligibility, cupping notes. The vision model only localizes defects, so none of those
can be computed truthfully yet, and several are outside the product's scope.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Self

from app.domain.errors import ErrorCode
from app.domain.taxonomy import DefectClass


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Pixel coordinates in the uploaded image: top-left (x1, y1), bottom-right (x2, y2)."""

    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True, slots=True)
class Detection:
    defect: DefectClass
    confidence: float  # model confidence in [0, 1]; not a probability of being correct
    box: BoundingBox


@dataclass(frozen=True, slots=True)
class ClassTally:
    defect: DefectClass
    count: int
    mean_confidence: float


@dataclass(frozen=True, slots=True)
class DetectionSummary:
    """Counts of *detections* (defect instances found). Not bean counts."""

    detection_count: int
    primary_count: int
    secondary_count: int
    by_class: tuple[ClassTally, ...]


@dataclass(frozen=True, slots=True)
class Coverage:
    """Which ECX defect classes the vision model scanned for, and which it did not."""

    scanned: tuple[DefectClass, ...]
    not_scanned: tuple[DefectClass, ...]


@dataclass(frozen=True, slots=True)
class BilingualText:
    en: str
    am: str


@dataclass(frozen=True, slots=True)
class Advisory:
    """AI-written guidance. `generator_model` records which model wrote it."""

    generator_model: str
    summary: BilingualText
    recommendations: tuple[BilingualText, ...]


class AssessmentStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ImageCheck:
    """Outcome of the vision service's "is this green coffee?" gate for an accepted photo.

    Photos that fail the gate never become assessments (see `NotCoffeeImageError`), so every
    stored check is a pass; the confidence and validator version are kept for traceability.
    """

    coffee_confidence: float
    validator_version: str


@dataclass(frozen=True, slots=True)
class AssessmentResult:
    model_version: str
    image_check: ImageCheck
    detections: tuple[Detection, ...]
    summary: DetectionSummary
    coverage: Coverage
    advisory: Advisory
    original_image_key: str | None
    annotated_image_key: str | None


@dataclass(frozen=True, slots=True)
class Assessment:
    """A completed assessment carries a result; a failed one carries an error code. Never both.

    `image_sha256` fingerprints the uploaded bytes so an idempotent retry can prove it is the
    same request, instead of silently returning another image's result.
    """

    assessment_id: str
    owner_id: str
    status: AssessmentStatus
    created_at: datetime
    processing_time_ms: int
    image_sha256: str
    result: AssessmentResult | None
    error_code: ErrorCode | None
    idempotency_key: str | None

    def __post_init__(self) -> None:
        if self.status is AssessmentStatus.COMPLETED:
            if self.result is None or self.error_code is not None:
                raise ValueError("a completed assessment needs a result and no error code")
        elif self.result is not None or self.error_code is None:
            raise ValueError("a failed assessment needs an error code and no result")

    @classmethod
    def completed(
        cls,
        *,
        assessment_id: str,
        owner_id: str,
        created_at: datetime,
        processing_time_ms: int,
        image_sha256: str,
        result: AssessmentResult,
        idempotency_key: str | None,
    ) -> Self:
        return cls(
            assessment_id=assessment_id,
            owner_id=owner_id,
            status=AssessmentStatus.COMPLETED,
            created_at=created_at,
            processing_time_ms=processing_time_ms,
            image_sha256=image_sha256,
            result=result,
            error_code=None,
            idempotency_key=idempotency_key,
        )

    @classmethod
    def failed(
        cls,
        *,
        assessment_id: str,
        owner_id: str,
        created_at: datetime,
        processing_time_ms: int,
        image_sha256: str,
        error_code: ErrorCode,
    ) -> Self:
        # A failed attempt never keeps the idempotency key, so a retry runs again.
        return cls(
            assessment_id=assessment_id,
            owner_id=owner_id,
            status=AssessmentStatus.FAILED,
            created_at=created_at,
            processing_time_ms=processing_time_ms,
            image_sha256=image_sha256,
            result=None,
            error_code=error_code,
            idempotency_key=None,
        )


@dataclass(frozen=True, slots=True)
class AssessmentPage:
    items: tuple[Assessment, ...]
    next_cursor: str | None
