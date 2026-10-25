"""Application errors. Pure Python (no Django/DRF) so domain code stays testable anywhere.

`ClientError`: the request cannot be served as sent; never recorded as a failed assessment.
`DependencyError`: something we depend on failed after we accepted the request; recorded.
`public_message` is safe to show a user; the `detail` passed to the constructor is for logs.
"""

from collections.abc import Mapping


class AppError(Exception):
    code = "INTERNAL_ERROR"
    http_status = 500
    public_message = "An unexpected error occurred."

    def __init__(
        self,
        detail: str | None = None,
        *,
        public_message: str | None = None,
        details: Mapping[str, str | float | bool] | None = None,
    ) -> None:
        super().__init__(detail or public_message or self.public_message)
        if public_message is not None:
            self.public_message = public_message
        self.details: dict[str, str | float | bool] = dict(details or {})
        self.assessment_id: str | None = None  # set once a failed attempt is recorded


class ClientError(AppError):
    http_status = 400


class InvalidImage(ClientError):
    code, http_status = "INVALID_IMAGE", 400
    public_message = "The uploaded file is not a readable image."


class UnsupportedImageFormat(ClientError):
    code, http_status = "UNSUPPORTED_FORMAT", 415
    public_message = "Unsupported image format. Use JPEG, PNG, or WEBP."


class ImageTooLarge(ClientError):
    code, http_status = "IMAGE_TOO_LARGE", 413
    public_message = "The image is too large."


class NotCoffeeImage(ClientError):
    """The vision service's gate decided the photo does not show green coffee beans."""

    code, http_status = "IMAGE_NOT_COFFEE", 422
    public_message = (
        "This photo does not appear to show green coffee beans. "
        "Please upload a clear photo of the sample."
    )

    def __init__(self, detail: str, *, coffee_confidence: float, threshold: float | None = None):
        details: dict[str, str | float | bool] = {
            "is_coffee": False,
            "coffee_confidence": coffee_confidence,
        }
        if threshold is not None:
            details["threshold"] = threshold
        super().__init__(detail, details=details)


class InvalidRequest(ClientError):
    code, http_status = "INVALID_REQUEST", 422
    public_message = "The request is invalid."


class IdempotencyKeyReused(ClientError):
    code, http_status = "IDEMPOTENCY_KEY_REUSED", 422
    public_message = "This Idempotency-Key was already used with a different image."


class InvalidCredentials(ClientError):
    code, http_status = "INVALID_CREDENTIALS", 401
    public_message = "Incorrect email or password."


class EmailAlreadyRegistered(ClientError):
    code, http_status = "EMAIL_ALREADY_REGISTERED", 409
    public_message = "An account with this email already exists."


class AssessmentNotFound(ClientError):
    code, http_status = "ASSESSMENT_NOT_FOUND", 404
    public_message = "Assessment not found."


class DependencyError(AppError):
    http_status = 502


class VisionUnavailable(DependencyError):
    code, http_status = "INFERENCE_FAILED", 502
    public_message = "The image analysis service is unavailable. Please try again."


class VisionTimeout(DependencyError):
    code, http_status = "INFERENCE_TIMEOUT", 504
    public_message = "The image analysis service took too long to respond. Please try again."


class VisionBadResponse(DependencyError):
    code, http_status = "INFERENCE_FAILED", 502
    public_message = "The image analysis service returned an unusable result."


class UnknownDefectClass(DependencyError):
    """Vision emitted a label our taxonomy does not know. Never guess a category."""

    code, http_status = "INFERENCE_FAILED", 502
    public_message = "The image analysis service returned a defect class this version does not recognise."


class AdvisoryFailed(DependencyError):
    code, http_status = "ADVISORY_FAILED", 502
    public_message = "The advisory service is unavailable or returned an unusable result."


class PersistenceFailed(DependencyError):
    code, http_status = "PERSISTENCE_FAILED", 503
    public_message = "The result could not be saved. Please try again."


class ModelReloadFailed(DependencyError):
    code, http_status = "MODEL_RELOAD_FAILED", 502
    public_message = "The model reload failed. The previously loaded model is still active."


# Codes produced by the framework layer (handler.py), listed so filters can validate against all.
ERROR_CODES = (
    "INVALID_IMAGE", "UNSUPPORTED_FORMAT", "IMAGE_TOO_LARGE", "IMAGE_NOT_COFFEE",
    "INVALID_REQUEST", "IDEMPOTENCY_KEY_REUSED", "AUTHENTICATION_REQUIRED", "INVALID_CREDENTIALS",
    "FORBIDDEN", "EMAIL_ALREADY_REGISTERED", "ASSESSMENT_NOT_FOUND", "RATE_LIMITED",
    "INFERENCE_FAILED", "INFERENCE_TIMEOUT", "ADVISORY_FAILED", "PERSISTENCE_FAILED",
    "MODEL_RELOAD_FAILED", "INTERNAL_ERROR",
)
