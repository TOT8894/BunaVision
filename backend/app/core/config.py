"""Application settings, read once from the environment (and an optional `.env`).

Rules this module enforces:

* Anything the service cannot run without has NO default. A missing value stops the process
  at startup with a message naming the variable, instead of failing on the first request.
* Tunables have a documented default, validated for range.
* Nothing here reads files or opens connections; importing it has no side effects.
"""

from enum import StrEnum
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_MIB = 1024 * 1024


class ConfigurationError(Exception):
    """Settings are individually valid but inconsistent with each other."""


class ImageStoreBackend(StrEnum):
    MEMORY = "memory"  # dev/test only: images are lost on restart and URLs are not fetchable
    S3 = "s3"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Required (no defaults) ---------------------------------------------------------
    vision_service_url: AnyHttpUrl
    gemini_api_key: SecretStr
    gemini_model: str = Field(min_length=1)
    """Check Google's Gemini deprecations page before choosing: models are retired."""
    image_store: ImageStoreBackend
    database_url: SecretStr
    """`postgresql+asyncpg://user:password@host:5432/dbname`. Secret: it contains the password."""
    jwt_secret: SecretStr
    """Signs access tokens. At least 32 characters; generate with `openssl rand -hex 32`."""

    # Required when image_store == "s3" (checked by the container at startup).
    s3_bucket: str | None = None
    s3_region: str | None = None
    s3_endpoint_url: AnyHttpUrl | None = None
    """Optional override for S3-compatible stores such as MinIO in local development."""

    # --- Optional, with documented defaults ---------------------------------------------
    cors_allowed_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)
    """Comma-separated list of allowed browser origins. Empty disables CORS."""

    max_image_bytes: int = Field(default=10 * _MIB, gt=0)
    max_image_pixels: int = Field(default=50_000_000, gt=0)
    min_image_side_px: int = Field(default=320, gt=0)
    """Provisional: confirm against the vision model's input requirements."""

    retain_original_image: bool = True
    image_url_ttl_s: int = Field(default=900, gt=0, le=604_800)

    db_pool_size: int = Field(default=5, gt=0)
    db_max_overflow: int = Field(default=5, ge=0)
    access_token_ttl_s: int = Field(default=3600, gt=0, le=86_400)

    max_assessments_per_user_per_hour: int = Field(default=30, gt=0)
    """Provisional: pick from real usage. Counts failed attempts too, since they cost compute."""
    max_concurrent_assessments: int = Field(default=4, gt=0)
    """Per process. Extra requests are rejected with 429 rather than queued."""

    vision_timeout_s: float = Field(default=30.0, gt=0)
    vision_reload_timeout_s: float = Field(default=60.0, gt=0)
    vision_connect_timeout_s: float = Field(default=3.0, gt=0)
    gemini_timeout_s: float = Field(default=30.0, gt=0)
    gemini_temperature: float = Field(default=0.2, ge=0, le=2)
    gemini_max_output_tokens: int = Field(default=8192, gt=0)
    """Thinking-enabled models spend part of this budget on reasoning; keep it generous."""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("database_url")
    @classmethod
    def _async_postgres_only(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must start with postgresql+asyncpg://")
        return value

    @field_validator("jwt_secret")
    @classmethod
    def _strong_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")
        return value

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


@lru_cache
def get_settings() -> Settings:
    """Load settings once per process. Called by the app factory, never at import time."""
    return Settings()  # type: ignore[call-arg]  # required fields come from the environment
