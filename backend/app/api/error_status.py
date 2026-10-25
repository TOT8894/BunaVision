"""HTTP status for every error code. Pure data: no framework imports, so it is easy to test."""

from app.domain.errors import ErrorCode

STATUS_BY_CODE: dict[ErrorCode, int] = {
    ErrorCode.INVALID_IMAGE: 400,
    ErrorCode.UNSUPPORTED_FORMAT: 415,
    ErrorCode.IMAGE_TOO_LARGE: 413,
    ErrorCode.IMAGE_NOT_COFFEE: 422,
    ErrorCode.INVALID_REQUEST: 422,
    ErrorCode.IDEMPOTENCY_KEY_REUSED: 422,
    ErrorCode.AUTHENTICATION_REQUIRED: 401,
    ErrorCode.INVALID_CREDENTIALS: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.EMAIL_ALREADY_REGISTERED: 409,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.ASSESSMENT_NOT_FOUND: 404,
    ErrorCode.INFERENCE_FAILED: 502,
    ErrorCode.INFERENCE_TIMEOUT: 504,
    ErrorCode.ADVISORY_FAILED: 502,
    ErrorCode.PERSISTENCE_FAILED: 503,
    ErrorCode.MODEL_RELOAD_FAILED: 502,
    ErrorCode.INTERNAL_ERROR: 500,
}
