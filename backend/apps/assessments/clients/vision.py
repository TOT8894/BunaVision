"""Sync HTTP client for the vision service: the only way this backend reaches it.

Sends image bytes, gets detections back; never imports vision code and knows nothing about how
detection works. Nothing is retried or papered over, so a vision problem can never look like
"zero detections".

* 400 with code IMAGE_NOT_COFFEE, or 200 with is_coffee == false -> NotCoffeeImage (client error)
* timeout -> VisionTimeout; connection error, 5xx, 429 -> VisionUnavailable
* any other non-200, or an unusable 200 body -> VisionBadResponse

Only the fields below are read; everything else vision sends is ignored, because counts and
categories are derived here from our own taxonomy.
"""

import base64
import binascii
from dataclasses import dataclass
from functools import lru_cache

import httpx
from django.conf import settings
from rest_framework import serializers

from apps.assessments.image_validation import ValidatedImage
from apps.common.errors import (
    ModelReloadFailed,
    NotCoffeeImage,
    VisionBadResponse,
    VisionTimeout,
    VisionUnavailable,
)
from apps.common.logging import request_id_var

NOT_COFFEE_CODE = "IMAGE_NOT_COFFEE"
_JPEG_SIGNATURE = b"\xff\xd8\xff"
_PREVIEW_CHARS = 300


@dataclass(frozen=True, slots=True)
class RawDetection:
    label: str
    confidence: float
    box: tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class VisionOutput:
    model_version: str
    validator_version: str
    coffee_confidence: float
    detections: tuple[RawDetection, ...]
    annotated_image: bytes | None  # JPEG bytes


class _Box(serializers.Serializer):
    x1 = serializers.FloatField()
    y1 = serializers.FloatField()
    x2 = serializers.FloatField()
    y2 = serializers.FloatField()

    def validate(self, attrs):  # noqa: ANN001, ANN201
        if not (attrs["x2"] > attrs["x1"] and attrs["y2"] > attrs["y1"]):
            raise serializers.ValidationError("box corners must satisfy x2 > x1 and y2 > y1")
        return attrs


class _Detection(serializers.Serializer):
    box = _Box()
    class_name = serializers.CharField()
    confidence = serializers.FloatField(min_value=0, max_value=1)


class _DetectResponse(serializers.Serializer):
    model_version = serializers.CharField()
    validator_version = serializers.CharField()
    is_coffee = serializers.BooleanField()
    coffee_confidence = serializers.FloatField(min_value=0, max_value=1)
    detected_beans = _Detection(many=True)  # vision's name; each item is one defect, not a bean
    annotated_image_base64 = serializers.CharField(required=False, allow_null=True)


class _RejectionDetail(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField(required=False, allow_blank=True)
    confidence = serializers.FloatField(min_value=0, max_value=1)
    threshold = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=1)


class _Rejection(serializers.Serializer):
    detail = _RejectionDetail()


class _Reload(serializers.Serializer):
    reloaded = serializers.BooleanField()
    engine = serializers.CharField()  # `model_path` is a server path: deliberately not read


@lru_cache(maxsize=1)
def get_http_client() -> httpx.Client:
    """One shared client (thread-safe). Tests patch this function."""
    return httpx.Client(
        base_url=settings.VISION_SERVICE_URL,
        timeout=httpx.Timeout(settings.VISION_TIMEOUT_S, connect=settings.VISION_CONNECT_TIMEOUT_S),
    )


def detect(image: ValidatedImage) -> VisionOutput:
    try:
        response = get_http_client().post(
            "/detect",
            # The user's filename is never forwarded; only a neutral one.
            files={"file": (f"upload.{image.format.extension}", image.data, image.format.content_type)},
            headers={"X-Request-ID": request_id_var.get()},
        )
    except httpx.TimeoutException as exc:
        raise VisionTimeout(f"vision request timed out: {exc!r}") from exc
    except httpx.TransportError as exc:
        raise VisionUnavailable(f"vision request failed: {exc!r}") from exc
    _raise_for_status(response)
    return _parse(response)


def reload_model() -> dict[str, object]:
    try:
        response = get_http_client().post(
            "/reload-model",
            timeout=settings.VISION_RELOAD_TIMEOUT_S,
            headers={"X-Request-ID": request_id_var.get()},
        )
    except httpx.TimeoutException as exc:
        # The reload may still finish on the vision side; the admin should check again.
        raise ModelReloadFailed(f"vision reload timed out: {exc!r}") from exc
    except httpx.TransportError as exc:
        raise ModelReloadFailed(f"vision reload request failed: {exc!r}") from exc
    if response.status_code != httpx.codes.OK:
        raise ModelReloadFailed(f"vision answered HTTP {response.status_code}: {response.text[:_PREVIEW_CHARS]}")
    try:
        body = _Reload(data=response.json())
    except ValueError as exc:
        raise ModelReloadFailed(f"vision reload reply is not JSON: {exc}") from exc
    if not body.is_valid():
        raise ModelReloadFailed(f"vision reload reply broke its contract: {body.errors}")
    return {"reloaded": body.validated_data["reloaded"], "engine": body.validated_data["engine"]}


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code == httpx.codes.OK:
        return
    if response.status_code == httpx.codes.BAD_REQUEST:
        _raise_if_not_coffee(response)
    detail = f"vision answered HTTP {response.status_code}: {response.text[:_PREVIEW_CHARS]}"
    if response.status_code >= 500 or response.status_code == httpx.codes.TOO_MANY_REQUESTS:
        raise VisionUnavailable(detail)
    raise VisionBadResponse(detail)


def _raise_if_not_coffee(response: httpx.Response) -> None:
    """Turn vision's coffee-gate rejection into a client error; otherwise do nothing."""
    try:
        rejection = _Rejection(data=response.json())
    except ValueError:
        return  # some other 400: reported as a bad vision response by the caller
    if rejection.is_valid() and rejection.validated_data["detail"]["code"] == NOT_COFFEE_CODE:
        detail = rejection.validated_data["detail"]
        raise NotCoffeeImage(
            f"vision coffee gate rejected the photo: {detail.get('message', '')}",
            coffee_confidence=detail["confidence"],
            threshold=detail.get("threshold"),
        )


def _parse(response: httpx.Response) -> VisionOutput:
    try:
        body = _DetectResponse(data=response.json())
    except ValueError as exc:
        raise VisionBadResponse(f"vision response is not JSON: {exc}") from exc
    if not body.is_valid():
        raise VisionBadResponse(f"vision response broke its contract: {body.errors}")
    data = body.validated_data
    if not data["is_coffee"]:
        raise NotCoffeeImage("vision reported is_coffee=false", coffee_confidence=data["coffee_confidence"])
    return VisionOutput(
        model_version=data["model_version"],
        validator_version=data["validator_version"],
        coffee_confidence=data["coffee_confidence"],
        detections=tuple(
            RawDetection(
                label=item["class_name"],
                confidence=item["confidence"],
                box=(item["box"]["x1"], item["box"]["y1"], item["box"]["x2"], item["box"]["y2"]),
            )
            for item in data["detected_beans"]
        ),
        annotated_image=_decode_annotated(data.get("annotated_image_base64")),
    )


def _decode_annotated(encoded: str | None) -> bytes | None:
    if encoded is None:
        return None
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise VisionBadResponse(f"annotated image is not valid base64: {exc}") from exc
    if not data.startswith(_JPEG_SIGNATURE):
        raise VisionBadResponse("annotated image is not a JPEG")
    return data
