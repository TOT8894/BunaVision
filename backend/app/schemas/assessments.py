"""Public assessment contract: what the frontend sees.

Counts are exact about what they count: a *detection* is one defect instance the vision model
located (one bounding box). Nothing here is a bean count, a grade, or a verified finding.
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.analysis import LimitationCode
from app.domain.errors import ErrorCode
from app.domain.taxonomy import DefectCategory


class ApiModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class BoundingBoxOut(ApiModel):
    """Pixel coordinates in the uploaded image; origin is the top-left corner."""

    x1: float
    y1: float
    x2: float
    y2: float


class DefectClassOut(ApiModel):
    key: str = Field(description="Stable machine identifier, e.g. 'full_black'.")
    name: str = Field(description="English display name.")
    category: DefectCategory


class DetectionOut(ApiModel):
    defect: DefectClassOut
    confidence: float = Field(
        ge=0, le=1, description="Model confidence. Not the probability the detection is correct."
    )
    box: BoundingBoxOut


class ClassTallyOut(ApiModel):
    defect: DefectClassOut
    count: int = Field(ge=0, description="Detections of this class.")
    mean_confidence: float = Field(ge=0, le=1, description="Mean model confidence over them.")


class SummaryOut(ApiModel):
    detection_count: int = Field(ge=0, description="All defect detections. Not a bean count.")
    primary_detection_count: int = Field(ge=0)
    secondary_detection_count: int = Field(ge=0)
    by_class: list[ClassTallyOut]


class CoverageOut(ApiModel):
    scanned: list[DefectClassOut] = Field(description="Classes the model looks for.")
    not_scanned: list[DefectClassOut] = Field(description="Classes it cannot detect.")


class LimitationOut(ApiModel):
    code: LimitationCode
    message: str = Field(description="English text; localize by `code` if needed.")


class BilingualTextOut(ApiModel):
    en: str
    am: str = Field(description="Amharic")


class AdvisoryOut(ApiModel):
    generator_model: str = Field(description="The AI model that wrote this text.")
    summary: BilingualTextOut
    recommendations: list[BilingualTextOut]


class ImagesOut(ApiModel):
    original_url: str | None = Field(description="Null when original images are not retained.")
    annotated_url: str | None
    expires_in_s: int = Field(
        description="Seconds the URLs stay valid. Fetch the assessment again for fresh ones."
    )


class ImageCheckOut(ApiModel):
    """The coffee gate. Photos that fail it are rejected with IMAGE_NOT_COFFEE instead."""

    is_coffee: Literal[True] = Field(
        default=True, description="Always true on a completed assessment."
    )
    coffee_confidence: float = Field(ge=0, le=1, description="Validator confidence it is coffee.")
    validator_version: str


class AssessmentResultOut(ApiModel):
    model_version: str = Field(description="Version of the vision model that found the defects.")
    image_check: ImageCheckOut
    summary: SummaryOut
    detections: list[DetectionOut]
    coverage: CoverageOut
    limitations: list[LimitationOut]
    advisory: AdvisoryOut
    images: ImagesOut


class CompletedAssessmentOut(ApiModel):
    assessment_id: str
    status: Literal["completed"] = "completed"
    created_at: datetime
    processing_time_ms: int = Field(ge=0)
    result: AssessmentResultOut


class FailedAssessmentOut(ApiModel):
    assessment_id: str
    status: Literal["failed"] = "failed"
    created_at: datetime
    processing_time_ms: int = Field(ge=0)
    error_code: ErrorCode


AssessmentOut = Annotated[
    CompletedAssessmentOut | FailedAssessmentOut, Field(discriminator="status")
]


class CompletedListItemOut(ApiModel):
    assessment_id: str
    status: Literal["completed"] = "completed"
    created_at: datetime
    model_version: str
    detection_count: int = Field(ge=0)
    primary_detection_count: int = Field(ge=0)
    secondary_detection_count: int = Field(ge=0)


class FailedListItemOut(ApiModel):
    assessment_id: str
    status: Literal["failed"] = "failed"
    created_at: datetime
    error_code: ErrorCode


AssessmentListItemOut = Annotated[
    CompletedListItemOut | FailedListItemOut, Field(discriminator="status")
]


class AssessmentListOut(ApiModel):
    items: list[AssessmentListItemOut]
    next_cursor: str | None = Field(description="Pass as `cursor` for the next page; null at the end.")
