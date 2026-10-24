"""Transport models for the vision service's responses.

These declare ONLY the fields the backend uses, and ignore everything else. The vision
service may add or drop other fields (`total_beans`, `healthy_beans`, `defect_counts`,
`category`, ...) without breaking us: counts and categories are derived here from the
detections, so there is one source of truth for each.

Note on naming: the vision service calls each detection a "bean" (`detected_beans`). It is
one defect instance, not a bean. The domain model uses the accurate word.
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


class VisionDetectResponse(BaseModel):
    """`POST /detect` 200 body. The coffee-gate fields are required: if vision stops sending
    them, the backend fails loudly rather than assume the photo was checked."""

    model_config = ConfigDict(extra="ignore")

    model_version: str = Field(min_length=1)
    validator_version: str = Field(min_length=1)
    is_coffee: bool
    coffee_confidence: float = Field(ge=0, le=1)
    detected_beans: list[VisionDetection]
    annotated_image_base64: str | None = None


class VisionRejectionDetail(BaseModel):
    """`detail` of the 400 vision sends when the coffee gate rejects a photo."""

    model_config = ConfigDict(extra="ignore")

    code: str
    message: str = ""
    confidence: float = Field(ge=0, le=1)
    threshold: float | None = Field(default=None, ge=0, le=1)


class VisionRejection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    detail: VisionRejectionDetail


class VisionReloadResponse(BaseModel):
    """`POST /reload-model` 200 body. `model_path` is deliberately not read: it is a server
    filesystem path and has no business in our API."""

    model_config = ConfigDict(extra="ignore")

    reloaded: bool
    engine: str = Field(min_length=1)
