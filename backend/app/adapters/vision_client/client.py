"""HTTP client for the vision service. Implements the `VisionDetector` and `VisionAdmin` ports.

The only way the backend reaches vision. It sends image bytes and gets detections back; it
never imports vision code and knows nothing about how detection works.

Error mapping for `/detect` (every failure becomes an explicit error; nothing is retried or
papered over here, so a vision problem can never look like "zero detections"):

* 400 with code IMAGE_NOT_COFFEE   -> NotCoffeeImageError (a client problem: wrong photo)
* 200 with is_coffee == false      -> NotCoffeeImageError (same, if vision ever answers so)
* timeout                          -> VisionTimeoutError
* connection error, 5xx, 429       -> VisionUnavailableError
* any other non-200 status         -> VisionBadResponseError (we sent something it rejects)
* 200 but unusable body            -> VisionBadResponseError
"""

import base64
import binascii

import httpx
from pydantic import ValidationError

from app.adapters.vision_client.models import (
    VisionDetectResponse,
    VisionRejection,
    VisionReloadResponse,
)
from app.core.logging import request_id_var
from app.domain.errors import (
    ModelReloadFailedError,
    NotCoffeeImageError,
    VisionBadResponseError,
    VisionTimeoutError,
    VisionUnavailableError,
)
from app.domain.models import BoundingBox, ImageCheck
from app.domain.operations import ModelReloadResult
from app.services.image_validation import ValidatedImage
from app.services.ports import RawDetection, VisionOutput

DETECT_PATH = "/detect"
RELOAD_PATH = "/reload-model"
UPLOAD_FIELD = "file"
REQUEST_ID_HEADER = "X-Request-ID"
NOT_COFFEE_CODE = "IMAGE_NOT_COFFEE"
_JPEG_SIGNATURE = b"\xff\xd8\xff"
_ERROR_BODY_PREVIEW_CHARS = 300


class HttpVisionDetector:
    def __init__(self, *, http: httpx.AsyncClient) -> None:
        """`http` carries the base URL and timeouts; its lifecycle belongs to the caller."""
        self._http = http

    async def detect(self, image: ValidatedImage) -> VisionOutput:
        try:
            response = await self._http.post(
                DETECT_PATH,
                # The user's filename is never forwarded; only a neutral one.
                files={
                    UPLOAD_FIELD: (
                        f"upload.{image.format.extension}",
                        image.data,
                        image.format.content_type,
                    )
                },
                headers={REQUEST_ID_HEADER: request_id_var.get()},
            )
        except httpx.TimeoutException as exc:
            raise VisionTimeoutError(f"vision request timed out: {exc!r}") from exc
        except httpx.TransportError as exc:
            raise VisionUnavailableError(f"vision request failed: {exc!r}") from exc

        _raise_for_status(response)
        return _parse(response)


class HttpVisionAdmin:
    def __init__(self, *, http: httpx.AsyncClient, timeout_s: float) -> None:
        self._http = http
        self._timeout_s = timeout_s

    async def reload_model(self) -> ModelReloadResult:
        try:
            response = await self._http.post(
                RELOAD_PATH,
                timeout=self._timeout_s,
                headers={REQUEST_ID_HEADER: request_id_var.get()},
            )
        except httpx.TimeoutException as exc:
            # The reload may still finish on the vision side; the admin should check again.
            raise ModelReloadFailedError(f"vision reload timed out: {exc!r}") from exc
        except httpx.TransportError as exc:
            raise ModelReloadFailedError(f"vision reload request failed: {exc!r}") from exc

        if response.status_code != httpx.codes.OK:
            preview = response.text[:_ERROR_BODY_PREVIEW_CHARS]
            raise ModelReloadFailedError(f"vision answered HTTP {response.status_code}: {preview}")
        try:
            body = VisionReloadResponse.model_validate_json(response.content)
        except ValidationError as exc:
            raise ModelReloadFailedError(f"vision reload reply broke its contract: {exc}") from exc
        return ModelReloadResult(reloaded=body.reloaded, engine=body.engine)


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code == httpx.codes.OK:
        return
    if response.status_code == httpx.codes.BAD_REQUEST:
        _raise_if_not_coffee(response)
    preview = response.text[:_ERROR_BODY_PREVIEW_CHARS]
    detail = f"vision answered HTTP {response.status_code}: {preview}"
    if response.status_code >= 500 or response.status_code == httpx.codes.TOO_MANY_REQUESTS:
        raise VisionUnavailableError(detail)
    raise VisionBadResponseError(detail)


def _raise_if_not_coffee(response: httpx.Response) -> None:
    """Turn vision's coffee-gate rejection into a client error; otherwise do nothing."""
    try:
        rejection = VisionRejection.model_validate_json(response.content)
    except ValidationError:
        return  # some other 400: the caller reports it as a bad vision response
    detail = rejection.detail
    if detail.code == NOT_COFFEE_CODE:
        raise NotCoffeeImageError(
            f"vision coffee gate rejected the photo: {detail.message}",
            coffee_confidence=detail.confidence,
            threshold=detail.threshold,
        )


def _parse(response: httpx.Response) -> VisionOutput:
    try:
        body = VisionDetectResponse.model_validate_json(response.content)
    except ValidationError as exc:
        raise VisionBadResponseError(f"vision response broke its contract: {exc}") from exc

    if not body.is_coffee:
        raise NotCoffeeImageError(
            "vision reported is_coffee=false", coffee_confidence=body.coffee_confidence
        )
    return VisionOutput(
        model_version=body.model_version,
        image_check=ImageCheck(
            coffee_confidence=body.coffee_confidence, validator_version=body.validator_version
        ),
        detections=tuple(
            RawDetection(
                label=item.class_name,
                confidence=item.confidence,
                box=BoundingBox(item.box.x1, item.box.y1, item.box.x2, item.box.y2),
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
