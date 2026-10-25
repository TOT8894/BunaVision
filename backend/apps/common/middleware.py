"""Request id, and an early size check so oversized uploads are refused before parsing."""

import re
import uuid

from django.conf import settings

from apps.common.logging import request_id_var
from apps.common.responses import envelope

_ACCEPTABLE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_MULTIPART_OVERHEAD_BYTES = 64 * 1024


class RequestIdMiddleware:
    def __init__(self, get_response):  # noqa: ANN001
        self.get_response = get_response

    def __call__(self, request):  # noqa: ANN001
        incoming = request.headers.get("X-Request-ID", "")
        request_id = incoming if _ACCEPTABLE_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        try:
            response = self.get_response(request)
        finally:
            request_id_var.reset(token)
        response["X-Request-ID"] = request_id
        return response


class BodySizeLimitMiddleware:
    """Rejects a declared Content-Length above the image limit (plus multipart overhead).

    Django's DATA_UPLOAD_MAX_MEMORY_SIZE does not cap file uploads, so this is the first layer;
    the view checks the real file size, and the reverse proxy should enforce the same limit.
    """

    def __init__(self, get_response):  # noqa: ANN001
        self.get_response = get_response

    def __call__(self, request):  # noqa: ANN001
        declared = request.META.get("CONTENT_LENGTH", "")
        if declared.isdigit() and int(declared) > settings.MAX_IMAGE_BYTES + _MULTIPART_OVERHEAD_BYTES:
            return envelope("IMAGE_TOO_LARGE", "The upload exceeds the size limit.", 413)
        return self.get_response(request)
