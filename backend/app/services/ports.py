"""Ports: what the services need from the outside world, stated as interfaces.

The service layer depends on these Protocols and on nothing concrete. Adapters in
`app.adapters` implement them, so the vision service, Gemini, S3, the database, password
hashing and token signing can each be replaced or faked without touching business logic.

Types here are deliberately transport-free: no HTTP, no base64, no SDK objects.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.domain.errors import ErrorCode
from app.domain.models import (
    Advisory,
    Assessment,
    AssessmentPage,
    AssessmentStatus,
    BoundingBox,
    Coverage,
    DetectionSummary,
    ImageCheck,
)
from app.domain.operations import ModelReloadResult, ModelVersionUsage, OutcomeCount
from app.domain.users import User
from app.services.image_validation import ValidatedImage

# --- Vision ------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RawDetection:
    """One detection as the vision service reports it, before taxonomy mapping."""

    label: str
    confidence: float
    box: BoundingBox


@dataclass(frozen=True, slots=True)
class VisionOutput:
    model_version: str
    image_check: ImageCheck
    detections: tuple[RawDetection, ...]
    annotated_image: bytes | None  # JPEG bytes, already decoded from transport encoding


class VisionDetector(Protocol):
    async def detect(self, image: ValidatedImage) -> VisionOutput:
        """Localize supported defects.

        Raises `NotCoffeeImageError` when the photo is not green coffee, and `DependencyError`
        subclasses when the vision service fails.
        """
        ...


class VisionAdmin(Protocol):
    async def reload_model(self) -> ModelReloadResult:
        """Ask the vision service to reload its model. Raises `DependencyError` on failure."""
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

    async def count_since(self, owner_id: str, since: datetime) -> int:
        """Assessments (completed or failed) the owner created at or after `since`."""
        ...


class AssessmentAdminQueries(Protocol):
    """Cross-user, read-only views for administrators."""

    async def get_any(self, assessment_id: str) -> Assessment | None: ...

    async def list_all(
        self,
        *,
        status: AssessmentStatus | None,
        error_code: ErrorCode | None,
        owner_id: str | None,
        limit: int,
        cursor: str | None,
    ) -> AssessmentPage:
        """Newest first, optionally filtered. Raises `InvalidRequestError` for a bad cursor."""
        ...

    async def model_version_usage(self) -> tuple[ModelVersionUsage, ...]: ...

    async def outcome_counts(self, since: datetime) -> tuple[OutcomeCount, ...]: ...


class UserRepository(Protocol):
    async def add(self, user: User) -> None:
        """Store a new user. Raises `EmailAlreadyRegisteredError` if the email is taken."""
        ...

    async def get(self, user_id: str) -> User | None: ...

    async def find_by_email(self, email: str) -> User | None:
        """`email` is already normalized."""
        ...


# --- Credentials -------------------------------------------------------------------------


class PasswordHasher(Protocol):
    @property
    def dummy_hash(self) -> str:
        """A valid hash of an unknown password, so unknown-user logins cost the same time."""
        ...

    async def hash(self, password: str) -> str: ...

    async def verify(self, password: str, password_hash: str) -> bool: ...


@dataclass(frozen=True, slots=True)
class IssuedToken:
    access_token: str
    expires_in_s: int


class TokenIssuer(Protocol):
    def issue(self, user_id: str) -> IssuedToken: ...

    def subject_of(self, token: str) -> str:
        """The user id inside a valid token. Raises `AuthenticationRequiredError` otherwise."""
        ...


# --- Time --------------------------------------------------------------------------------


class Clock(Protocol):
    def now(self) -> datetime: ...

    def monotonic(self) -> float: ...
