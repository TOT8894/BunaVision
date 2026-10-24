"""Maps exceptions to the error envelope in one place. Routes never build error responses."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.envelope import error_response
from app.api.error_status import STATUS_BY_CODE
from app.domain.errors import BunaVisionError, ClientInputError, ErrorCode

logger = logging.getLogger(__name__)

_MAX_VALIDATION_ISSUES = 5
_UNAUTHORIZED = 401


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(BunaVisionError, _domain_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(Exception, _unexpected_error)


async def _domain_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, BunaVisionError):  # narrows the type; Starlette routes by class
        raise exc
    if not isinstance(exc, ClientInputError):
        logger.warning("request failed: %s (%s)", exc.code, exc)
    status_code = STATUS_BY_CODE[exc.code]
    return error_response(
        code=exc.code,
        message=exc.public_message,
        status_code=status_code,
        assessment_id=exc.assessment_id,
        details=exc.public_details,
        headers={"WWW-Authenticate": "Bearer"} if status_code == _UNAUTHORIZED else None,
    )


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    issues = "; ".join(
        f"{'.'.join(str(part) for part in issue['loc'])}: {issue['msg']}"
        for issue in exc.errors()[:_MAX_VALIDATION_ISSUES]
    )
    return error_response(
        code=ErrorCode.INVALID_REQUEST,
        message=f"Invalid request. {issues}",
        status_code=STATUS_BY_CODE[ErrorCode.INVALID_REQUEST],
    )


async def _http_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise exc
    return error_response(
        code=ErrorCode.INVALID_REQUEST, message=str(exc.detail), status_code=exc.status_code
    )


async def _unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled error", exc_info=exc)
    return error_response(
        code=ErrorCode.INTERNAL_ERROR,
        message=BunaVisionError.public_message,
        status_code=STATUS_BY_CODE[ErrorCode.INTERNAL_ERROR],
    )
