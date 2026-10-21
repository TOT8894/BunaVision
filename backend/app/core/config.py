"""Application settings, read once from the environment (and an optional `.env`).

Rules this module enforces:

* Anything the service cannot run without has NO default. A missing value stops the process
  at startup with a message naming the variable, instead of failing on the first request.
* Tunables have a documented default, validated for range.
* Nothing here reads files or opens connections; importing it has no side effects.
"""

from enum import StrEnum
from functools import lru_cache
from typing import Annotated, Literal, Self

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_MIB = 1024 * 1024
MULTIPART_OVERHEAD_BYTES = _MIB  # headroom above the image limit for multipart framing


class ImageStoreBackend(StrEnum):
    MEMORY = "memory"  # dev/test only: images vanish on restart and URLs are not fetchable
    S3 = "s3"


class AssessmentStoreBackend(StrEnum):
    MEMORY = "memory"  # dev/test only: records vanish on restart. Database choice is still open.


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Required (no defaults) ---------------------------------------------------------
    vision_service_url: AnyHttpUrl
    gemini_api_key: SecretStr
    gemini_model: str = Field(min_length=1)
    """Model ids get retired (gemini-2.5-flash has a published shutdown date). Check
    https://ai.google.dev/gemini-api/docs/deprecations before choosing one."""
    image_store: ImageStoreBackend
    assessment_store: AssessmentStoreBackend

    # Required when image_store == "s3" (enforced below).
    s3_bucket: str | None = None
    s3_region: str | None = None
    s3_endpoint_url: AnyHttpUrl | None = None
    """Optional override for S3-compatible stores such as MinIO in local development."""

    # --- Optional, with documented defaults ---------------------------------------------
    cors_allowed_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)
    """Comma-separated browser origins. Empty means no cross-origin access."""

    max_image_bytes: int = Field(default=10 * _MIB, gt=0)
    max_image_pixels: int = Field(default=40_000_000, gt=0)
    """Decoded images cost ~3-4 bytes/pixel in memory; keep this bounded."""
    min_image_side_px: int = Field(default=320, gt=0)
    """Provisional: confirm against the vision model's input requirements."""

    retain_original_image: bool = True
    image_url_ttl_s: int = Field(default=900, gt=0, le=604_800)

    vision_timeout_s: float = Field(default=30.0, gt=0)
    vision_connect_timeout_s: float = Field(default=3.0, gt=0)
    gemini_timeout_s: float = Field(default=30.0, gt=0)
    gemini_temperature: float = Field(default=0.2, ge=0, le=2)
    gemini_max_output_tokens: int = Field(default=8192, gt=0)
    """Thinking-enabled models spend part of this budget on reasoning; keep it generous."""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @property
    def max_body_bytes(self) -> int:
        return self.max_image_bytes + MULTIPART_OVERHEAD_BYTES

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("cors_allowed_origins")
    @classmethod
    def _reject_wildcard(cls, origins: list[str]) -> list[str]:
        if "*" in origins:
            raise ValueError("wildcard origins are not allowed; list the real frontend origins")
        return origins

    @model_validator(mode="after")
    def _s3_needs_bucket_and_region(self) -> Self:
        if self.image_store is ImageStoreBackend.S3 and not (self.s3_bucket and self.s3_region):
            raise ValueError("S3_BUCKET and S3_REGION are required when IMAGE_STORE=s3")
        return self


@lru_cache
def get_settings() -> Settings:
    """Load settings once per process. Called by the app factory, never at import time."""
    return Settings()  # type: ignore[call-arg]  # required fields come from the environment
