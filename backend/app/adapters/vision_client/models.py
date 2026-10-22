"""Transport models for the vision service's `POST /detect` response.

Declared from `contracts/vision-api/` (the vision OpenAPI). Only the fields the backend uses
are modelled; everything else is ignored, so vision can add fields without breaking us.

Deliberately NOT consumed: `total_beans` and `healthy_beans` (vision cannot count healthy
beans and reports -1), `defect_counts` (we derive counts from the detections, so there is one
source of truth), and `confidence`/`category` as decisions (the taxonomy decides categories;
vision's `category` is read only to detect drift).

`detected_beans` is REQUIRED here even though the vision schema gives it a default: a missing
list must read as a broken response, never as "zero detections". The service calls each
detection a "bean"; it is one defect instance, and the domain model says so.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class VisionBox(BaseModel):
    model_config = ConfigDict(extra="ignore")

    x1: float
    y1: float
    x2: float
    y2: float

    @model_validator(mode="after")
    def _corners_are_ordered(self) -> Self:
        if not (self.x2 > self.x1 and self.y2 > self.y1):
            raise ValueError("bounding box corners must satisfy x2 > x1 and y2 > y1")
        return self


class VisionDetection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    box: VisionBox
    class_name: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    category: str = Field(min_length=1)


class VisionDetectResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    model_version: str = Field(min_length=1)
    defect_beans: int = Field(ge=0)
    detected_beans: list[VisionDetection]
    annotated_image_base64: str | None = None

    @model_validator(mode="after")
    def _count_matches_list(self) -> Self:
        # Integrity check: a truncated list must not pass as a smaller, valid result.
        if self.defect_beans != len(self.detected_beans):
            raise ValueError(
                f"defect_beans={self.defect_beans} but {len(self.detected_beans)} detections listed"
            )
        return self
