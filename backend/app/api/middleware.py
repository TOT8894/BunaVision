"""Pure-ASGI middleware (no BaseHTTPMiddleware, which buffers bodies and breaks streaming).

* `RequestContextMiddleware` gives every request an id, exposes it to logs, and returns it in
  the `X-Request-ID` response header.
* `RequestSizeLimitMiddleware` stops oversized bodies BEFORE they are parsed or spooled:
  first from the declared Content-Length, then by counting bytes as they stream in, which
  also covers chunked uploads that declare no length.
"""

import re
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.envelope import error_response
from app.api.error_status import STATUS_BY_CODE
from app.core.logging import request_id_var
from app.domain.errors import ErrorCode

REQUEST_ID_HEADER = "X-Request-ID"
_ACCEPTABLE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _header(scope: Scope, name: bytes) -> str | None:
    for key, value in scope["headers"]:
        if key == name:
            decoded: str = value.decode("latin-1")
            return decoded
    return None


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = _header(scope, REQUEST_ID_HEADER.lower().encode())
        request_id = incoming if incoming and _ACCEPTABLE_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        token = request_id_var.set(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            request_id_var.reset(token)


class _BodyTooLargeError(Exception):
    """Raised from the receive channel when a body outgrows the limit."""


class RequestSizeLimitMiddleware:
    def __init__(self, app: ASGIApp, *, max_body_bytes: int) -> None:
        self.app = app
        self._max = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = _declared_length(scope)
        if declared is not None and declared > self._max:
            await self._reject(scope, receive, send)
            return

        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self._max:
                    raise _BodyTooLargeError
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except _BodyTooLargeError:
            if response_started:
                raise
            await self._reject(scope, receive, send)

    async def _reject(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = error_response(
            code=ErrorCode.IMAGE_TOO_LARGE,
            message="The upload exceeds the size limit.",
            status_code=STATUS_BY_CODE[ErrorCode.IMAGE_TOO_LARGE],
        )
        await response(scope, receive, send)


def _declared_length(scope: Scope) -> int | None:
    value = _header(scope, b"content-length")
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None  # malformed header: the streaming count still enforces the limit
