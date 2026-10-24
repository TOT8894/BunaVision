import unittest

import httpx
from starlette.responses import Response

from app.api.middleware import RequestSizeLimitMiddleware


class RequestSizeLimitTests(unittest.IsolatedAsyncioTestCase):
    async def test_chunked_oversized_upload_returns_413_error_envelope(self) -> None:
        async def consume_body(scope, receive, send):  # noqa: ANN001
            while True:
                message = await receive()
                if not message.get("more_body", False):
                    break
            await Response(status_code=200)(scope, receive, send)

        app = RequestSizeLimitMiddleware(consume_body, max_body_bytes=3)

        async def chunks():
            yield b"12"
            yield b"34"

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://backend"
        ) as client:
            response = await client.post("/upload", content=chunks())

        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["error"]["code"], "IMAGE_TOO_LARGE")
