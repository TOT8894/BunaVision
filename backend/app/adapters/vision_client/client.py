"""HTTP client for the vision service. Implements the `VisionDetector` port.

The only way the backend reaches vision. It sends image bytes and gets detections back; it
never imports vision code and knows nothing about how detection works. The confidence
threshold is vision's own business, so it is not sent.

Error mapping (every failure becomes an explicit `DependencyError`; nothing is retried or
papered over here, so a vision problem can never look like "zero detections"):

* timeout                       -> VisionTimeoutError
* connection error, 5xx, 429    -> VisionUnavailableError
* any other non-200 status      -> VisionBadResponseError
* 200 but unusable body         -> VisionBadResponseError
"""

import base64
import binascii

import httpx
from pydantic import ValidationError

from app.adapters.vision_client.models import VisionDetectResponse
from app.core.logging import request_id_var
from app.domain.errors import (
    VisionBadResponseError,
    VisionTimeoutError,
    VisionUnavailableError,
)
from app.domain.models import BoundingBox
from app.services.image_validation import ValidatedImage
from app.services.ports import RawDetection, VisionOutput

DETECT_PATH = "/detect"
UPLOAD_FIELD = "file"  # from contracts/vision-api: Body_detect_defects_detect_post.file
REQUEST_ID_HEADER = "X-Request-ID"
_JPEG_SIGNATURE = b"\xff\xd8\xff"
_ERROR_BODY_PREVIEW_CHARS = 300


class HttpVisionDetector:
    def __init__(self, *, http: httpx.AsyncClient) -> None:
        """`http` carries the base URL and timeouts; its lifecycle belongs to the caller."""
        self._http = http

    async def detect(self, image: ValidatedImage) -> VisionOutput:
        # The user's filename is never forwarded; only a neutral one.
        upload = (f"upload.{image.format.extension}", image.data, image.format.content_type)
        try:
            response = await self._http.post(
                DETECT_PATH,
                files={UPLOAD_FIELD: upload},
                headers={REQUEST_ID_HEADER: request_id_var.get()},
            )
        except httpx.TimeoutException as exc:
            raise VisionTimeoutError(f"vision request timed out: {exc!r}") from exc
        except httpx.TransportError as exc:
            raise VisionUnavailableError(f"vision request failed: {exc!r}") from exc

        _raise_for_status(response)
        return _parse(response)


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code == httpx.codes.OK:
        return
    preview = response.text[:_ERROR_BODY_PREVIEW_CHARS]
    detail = f"vision answered HTTP {response.status_code}: {preview}"
    if response.status_code >= 500 or response.status_code == httpx.codes.TOO_MANY_REQUESTS:
        raise VisionUnavailableError(detail)
    raise VisionBadResponseError(detail)


def _parse(response: httpx.Response) -> VisionOutput:
    try:
        body = VisionDetectResponse.model_validate_json(response.content)
    except ValidationError as exc:
        raise VisionBadResponseError(f"vision response broke its contract: {exc}") from exc

    return VisionOutput(
        model_version=body.model_version,
        detections=tuple(
            RawDetection(
                label=item.class_name,
                confidence=item.confidence,
                box=BoundingBox(item.box.x1, item.box.y1, item.box.x2, item.box.y2),
                reported_category=item.category,
            )
            for item in body.detected_beans
        ),
        annotated_image=_decode_annotated(body.annotated_image_base64),
    )


def _decode_annotated(encoded: str | None) -> bytes | None:
    if encoded is None:
        return None
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise VisionBadResponseError(f"annotated image is not valid base64: {exc}") from exc
    if not data.startswith(_JPEG_SIGNATURE):
        raise VisionBadResponseError("annotated image is not a JPEG")
    return data
