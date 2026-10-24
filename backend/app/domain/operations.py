"""Operational vocabulary for the admin side: limits, usage and outcomes."""

from dataclasses import dataclass
from datetime import datetime

from app.domain.errors import ErrorCode
from app.domain.models import AssessmentStatus


@dataclass(frozen=True, slots=True)
class OperationalLimits:
    """What the running service actually enforces. Built once from settings."""

    max_image_bytes: int
    max_image_pixels: int
    min_image_side_px: int
    max_assessments_per_user_per_hour: int
    max_concurrent_assessments: int
    vision_timeout_s: float
    gemini_timeout_s: float
    image_url_ttl_s: int
    retain_original_image: bool


@dataclass(frozen=True, slots=True)
class ModelVersionUsage:
    """How often a (vision model, coffee validator) version pair produced a completed result."""

    model_version: str
    validator_version: str
    assessments: int
    first_seen: datetime
    last_seen: datetime


@dataclass(frozen=True, slots=True)
class OutcomeCount:
    status: AssessmentStatus
    error_code: ErrorCode | None
    count: int


@dataclass(frozen=True, slots=True)
class OutcomeOverview:
    since: datetime
    window_hours: int
    outcomes: tuple[OutcomeCount, ...]


@dataclass(frozen=True, slots=True)
class ModelReloadResult:
    reloaded: bool
    engine: str
