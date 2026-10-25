"""Domain errors.

Every failure the application can raise on purpose is a `BunaVisionError` with a stable
`ErrorCode`. The HTTP layer maps codes to status codes; nothing here knows about HTTP.

Two families matter to the workflow:

* `ClientInputError`: the request cannot be served as sent (bad input, not signed in, no
  permission, over quota). Never recorded as a failed assessment, because no assessment was
  attempted.
* `DependencyError`: something we depend on (vision service, Gemini, storage) failed after
  we accepted the request. Recorded as a failed assessment.

`detail` is for logs and may contain internals. `public_message` is safe to show a user.
"""

from collections.abc import Mapping
from enum import StrEnum


class ErrorCode(StrEnum):
    """Machine-readable error vocabulary shared with the frontend."""

    INVALID_IMAGE = "INVALID_IMAGE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    IMAGE_TOO_LARGE = "IMAGE_TOO_LARGE"
    IMAGE_NOT_COFFEE = "IMAGE_NOT_COFFEE"
    INVALID_REQUEST = "INVALID_REQUEST"
    IDEMPOTENCY_KEY_REUSED = "IDEMPOTENCY_KEY_REUSED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    FORBIDDEN = "FORBIDDEN"
    EMAIL_ALREADY_REGISTERED = "EMAIL_ALREADY_REGISTERED"
    RATE_LIMITED = "RATE_LIMITED"
    ASSESSMENT_NOT_FOUND = "ASSESSMENT_NOT_FOUND"
    INFERENCE_FAILED = "INFERENCE_FAILED"
    INFERENCE_TIMEOUT = "INFERENCE_TIMEOUT"
    ADVISORY_FAILED = "ADVISORY_FAILED"
    PERSISTENCE_FAILED = "PERSISTENCE_FAILED"
    MODEL_RELOAD_FAILED = "MODEL_RELOAD_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class BunaVisionError(Exception):
    """Base class for every intentional application error."""

    code: ErrorCode = ErrorCode.INTERNAL_ERROR
    public_message: str = "An unexpected error occurred."

    def __init__(
        self,
        detail: str | None = None,
        *,
        public_message: str | None = None,
        public_details: Mapping[str, str | float | bool] | None = None,
    ) -> None:
        super().__init__(detail or public_message or self.public_message)
        if public_message is not None:
            self.public_message = public_message
        # Machine-readable facts that are safe to show the caller (e.g. the coffee check).
        self.public_details: dict[str, str | float | bool] = dict(public_details or {})
        # Set by the workflow once an assessment id exists, so the API can echo it.
        self.assessment_id: str | None = None


class InvariantViolationError(BunaVisionError):
    """A state the code guarantees cannot happen did happen. Always a bug, never user error."""


# --- Caller mistakes -------------------------------------------------------------------


class ClientInputError(BunaVisionError):
    """The request cannot be processed as sent."""


class InvalidImageError(ClientInputError):
    code = ErrorCode.INVALID_IMAGE
    public_message = "The uploaded file is not a readable image."


class UnsupportedImageFormatError(ClientInputError):
    code = ErrorCode.UNSUPPORTED_FORMAT
    public_message = "Unsupported image format. Use JPEG, PNG, or WEBP."


class ImageTooLargeError(ClientInputError):
    code = ErrorCode.IMAGE_TOO_LARGE
    public_message = "The image is too large."


class NotCoffeeImageError(ClientInputError):
    """The vision service's gate decided the photo does not show green coffee beans."""

    code = ErrorCode.IMAGE_NOT_COFFEE
    public_message = (
        "This photo does not appear to show green coffee beans. "
        "Please upload a clear photo of the sample."
    )

    def __init__(
        self, detail: str, *, coffee_confidence: float, threshold: float | None = None
    ) -> None:
        details: dict[str, str | float | bool] = {
            "is_coffee": False,
            "coffee_confidence": coffee_confidence,
        }
        if threshold is not None:
            details["threshold"] = threshold
        super().__init__(detail, public_details=details)


class InvalidRequestError(ClientInputError):
    code = ErrorCode.INVALID_REQUEST
    public_message = "The request is invalid."


class IdempotencyKeyReusedError(ClientInputError):
    code = ErrorCode.IDEMPOTENCY_KEY_REUSED
    public_message = "This Idempotency-Key was already used with a different image."


class AuthenticationRequiredError(ClientInputError):
    code = ErrorCode.AUTHENTICATION_REQUIRED
    public_message = "Authentication is required. Please sign in."


class InvalidCredentialsError(ClientInputError):
    code = ErrorCode.INVALID_CREDENTIALS
    public_message = "Incorrect email or password."


class ForbiddenError(ClientInputError):
    code = ErrorCode.FORBIDDEN
    public_message = "You do not have permission to do this."


class EmailAlreadyRegisteredError(ClientInputError):
    code = ErrorCode.EMAIL_ALREADY_REGISTERED
    public_message = "An account with this email already exists."


class RateLimitedError(ClientInputError):
    code = ErrorCode.RATE_LIMITED
    public_message = "Too many requests. Please try again later."


class AssessmentNotFoundError(ClientInputError):
    code = ErrorCode.ASSESSMENT_NOT_FOUND
    public_message = "Assessment not found."


# --- Failures of things we depend on ---------------------------------------------------


class DependencyError(BunaVisionError):
    """A downstream system failed or broke its contract."""


class VisionUnavailableError(DependencyError):
    code = ErrorCode.INFERENCE_FAILED
    public_message = "The image analysis service is unavailable. Please try again."


class VisionTimeoutError(DependencyError):
    code = ErrorCode.INFERENCE_TIMEOUT
    public_message = "The image analysis service took too long to respond. Please try again."


class VisionBadResponseError(DependencyError):
    """The vision service answered, but not according to its contract."""

    code = ErrorCode.INFERENCE_FAILED
    public_message = "The image analysis service returned an unusable result."


class UnknownDefectClassError(DependencyError):
    """Vision emitted a label our taxonomy does not know. Never guess a category."""

    code = ErrorCode.INFERENCE_FAILED
    public_message = (
        "The image analysis service returned a defect class this version does not recognise."
    )


class AdvisoryUnavailableError(DependencyError):
    code = ErrorCode.ADVISORY_FAILED
    public_message = "The advisory service is unavailable. Please try again."


class AdvisoryInvalidError(DependencyError):
    code = ErrorCode.ADVISORY_FAILED
    public_message = "The advisory service returned an unusable result."


class PersistenceError(DependencyError):
    code = ErrorCode.PERSISTENCE_FAILED
    public_message = "The result could not be saved. Please try again."


class ModelReloadFailedError(DependencyError):
    code = ErrorCode.MODEL_RELOAD_FAILED
    public_message = "The model reload failed. The previously loaded model is still active."


class DuplicateIdempotencyKeyError(BunaVisionError):
    """Control-flow signal from the repository: this owner already used this key.

    Raised when two requests with the same key race. The workflow catches it and replays
    the stored result; it must never reach the API layer.
    """
