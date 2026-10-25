"""Administrator-only views. Never exposed to ordinary users."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.errors import ErrorCode
from app.domain.models import AssessmentStatus


class AdminModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class AdminAssessmentOut(AdminModel):
    """One recorded attempt, from any user. Enough to troubleshoot a failure."""

    assessment_id: str
    owner_id: str
    status: AssessmentStatus
    created_at: datetime
    processing_time_ms: int = Field(ge=0)
    error_code: ErrorCode | None = Field(description="Set when status is `failed`.")
    model_version: str | None = Field(description="Vision model version; set when completed.")
    validator_version: str | None = Field(description="Coffee validator version; set when completed.")
    detection_count: int | None = Field(description="Defect detections; set when completed.")


class AdminAssessmentListOut(AdminModel):
    items: list[AdminAssessmentOut]
    next_cursor: str | None


class ModelVersionUsageOut(AdminModel):
    model_version: str
    validator_version: str
    assessments: int = Field(ge=1, description="Completed assessments produced by this pair.")
    first_seen: datetime
    last_seen: datetime


class ModelVersionsOut(AdminModel):
    versions: list[ModelVersionUsageOut]


class OutcomeCountOut(AdminModel):
    status: AssessmentStatus
    error_code: ErrorCode | None
    count: int = Field(ge=1)


class OverviewOut(AdminModel):
    since: datetime
    window_hours: int
    outcomes: list[OutcomeCountOut]


class LimitsOut(AdminModel):
    """What the running service enforces. Read-only: change them through configuration."""

    max_image_bytes: int
    max_image_pixels: int
    min_image_side_px: int
    max_assessments_per_user_per_hour: int
    max_concurrent_assessments: int
    vision_timeout_s: float
    gemini_timeout_s: float
    image_url_ttl_s: int
    retain_original_image: bool


class ModelReloadOut(AdminModel):
    reloaded: bool
    engine: str
