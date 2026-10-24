"""The one error envelope every failing response uses."""

from pydantic import BaseModel, ConfigDict, Field

from app.domain.errors import ErrorCode


class ErrorBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: ErrorCode
    message: str = Field(description="Safe to show to a user.")
    request_id: str = Field(description="Quote this when reporting a problem.")
    assessment_id: str | None = Field(
        default=None, description="Set when a failed attempt was recorded under an id."
    )
    details: dict[str, str | float | bool] | None = Field(
        default=None,
        description=(
            "Machine-readable facts about the error. For IMAGE_NOT_COFFEE: `is_coffee` (false), "
            "`coffee_confidence`, and `threshold` when known."
        ),
    )


class ErrorResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    error: ErrorBody
