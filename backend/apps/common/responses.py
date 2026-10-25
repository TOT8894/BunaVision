"""The one error envelope. Used by the DRF handler and by middleware."""

from collections.abc import Mapping

from django.http import JsonResponse

from apps.common.logging import request_id_var


def envelope(
    code: str,
    message: str,
    status: int,
    *,
    assessment_id: str | None = None,
    details: Mapping[str, str | float | bool] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JsonResponse:
    body = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id_var.get(),
            "assessment_id": assessment_id,
            "details": dict(details) if details else None,
        }
    }
    response = JsonResponse(body, status=status)
    for name, value in (headers or {}).items():
        response[name] = value
    return response
