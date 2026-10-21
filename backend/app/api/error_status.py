"""HTTP status for every error code. One table, checked by a test so no code is forgotten."""

from app.domain.errors import ErrorCode

STATUS_BY_CODE: dict[ErrorCode, int] = {
    ErrorCode.INVALID_IMAGE: 400,
    ErrorCode.UNSUPPORTED_FORMAT: 415,
    ErrorCode.IMAGE_TOO_LARGE: 413,
    ErrorCode.INVALID_REQUEST: 422,
    ErrorCode.IDEMPOTENCY_KEY_REUSED: 409,
    ErrorCode.ASSESSMENT_NOT_FOUND: 404,
    ErrorCode.INFERENCE_FAILED: 502,
    ErrorCode.INFERENCE_TIMEOUT: 504,
    ErrorCode.ADVISORY_FAILED: 502,
    ErrorCode.PERSISTENCE_FAILED: 503,
    ErrorCode.INTERNAL_ERROR: 500,
}
