"""Small helper so routers document their error responses the same way."""

from typing import Any

from app.schemas.errors import ErrorResponse


def error_responses(*statuses: int) -> dict[int | str, dict[str, Any]]:
    return {
        status: {"model": ErrorResponse, "description": "Error. See the `error.code` field."}
        for status in statuses
    }
