"""DRF exception handler: every error leaves the API in the same envelope.

Domain errors (`AppError`) carry their own code and status. DRF's and Django's built-in errors
are mapped to the same codes the FastAPI backend used, so the frontend sees no difference.
"""

import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.db import Error as DatabaseError
from django.http import Http404
from rest_framework import exceptions as drf

from apps.common.errors import AppError, ClientError
from apps.common.responses import envelope

logger = logging.getLogger(__name__)
_MAX_ISSUES = 5


def _issues(detail, prefix: str = ""):  # noqa: ANN001, ANN202
    if isinstance(detail, dict):
        for key, value in detail.items():
            yield from _issues(value, f"{prefix}{key}.")
    elif isinstance(detail, list):
        for item in detail:
            yield from _issues(item, prefix)
    else:
        yield f"{prefix.rstrip('.')}: {detail}" if prefix else str(detail)


def exception_handler(exc, context):  # noqa: ANN001, ANN201
    if isinstance(exc, AppError):
        if not isinstance(exc, ClientError):
            logger.warning("request failed: %s (%s)", exc.code, exc)
        return envelope(
            exc.code, exc.public_message, exc.http_status,
            assessment_id=exc.assessment_id, details=exc.details,
            headers={"WWW-Authenticate": "Bearer"} if exc.http_status == 401 else None,
        )
    if isinstance(exc, (drf.NotAuthenticated, drf.AuthenticationFailed)):
        return envelope(
            "AUTHENTICATION_REQUIRED", "Authentication is required. Please sign in.", 401,
            headers={"WWW-Authenticate": "Bearer"},
        )
    if isinstance(exc, (drf.PermissionDenied, DjangoPermissionDenied)):
        return envelope("FORBIDDEN", "You do not have permission to do this.", 403)
    if isinstance(exc, drf.Throttled):
        headers = {"Retry-After": str(int(exc.wait))} if exc.wait else None
        return envelope("RATE_LIMITED", "Too many requests. Please try again later.", 429, headers=headers)
    if isinstance(exc, drf.ValidationError):
        issues = "; ".join(list(_issues(exc.detail))[:_MAX_ISSUES])
        return envelope("INVALID_REQUEST", f"Invalid request. {issues}", 422)
    if isinstance(exc, (drf.NotFound, Http404)):
        return envelope("INVALID_REQUEST", "Not found.", 404)
    if isinstance(exc, drf.ParseError):
        return envelope("INVALID_REQUEST", "The request body could not be parsed.", 422)
    if isinstance(exc, drf.APIException):  # 405, 406, 415 and friends
        return envelope("INVALID_REQUEST", str(exc.detail), exc.status_code)
    if isinstance(exc, DatabaseError):
        logger.error("database error", exc_info=exc)
        return envelope("PERSISTENCE_FAILED", "The result could not be saved. Please try again.", 503)
    logger.error("unhandled error", exc_info=exc)
    return envelope("INTERNAL_ERROR", AppError.public_message, 500)
