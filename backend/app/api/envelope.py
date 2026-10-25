"""Builds the one error envelope. Shared by error handlers and middleware."""

from collections.abc import Mapping

from fastapi.responses import JSONResponse

from app.core.logging import request_id_var
from app.domain.errors import ErrorCode
from app.schemas.errors import ErrorBody, ErrorResponse


def error_response(
    *,
    code: ErrorCode,
    message: str,
    status_code: int,
    assessment_id: str | None = None,
    details: Mapping[str, str | float | bool] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            request_id=request_id_var.get(),
            assessment_id=assessment_id,
            details=dict(details) if details else None,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json"),
        headers=dict(headers) if headers else None,
    )
