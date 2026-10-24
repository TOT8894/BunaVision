import asyncio
import unittest

from starlette.requests import Request

from app.api.error_handlers import _domain_error
from app.api.error_status import STATUS_BY_CODE
from app.domain.errors import BunaVisionError, ErrorCode, RateLimitedError


def _all_error_classes(base: type[BunaVisionError]) -> list[type[BunaVisionError]]:
    found = [base]
    for sub in base.__subclasses__():
        found.extend(_all_error_classes(sub))
    return found


class ErrorStatusTests(unittest.TestCase):
    def test_every_error_code_has_an_http_status(self) -> None:
        self.assertEqual(set(STATUS_BY_CODE), set(ErrorCode))

    def test_statuses_are_client_or_server_errors(self) -> None:
        for code, status in STATUS_BY_CODE.items():
            with self.subTest(code=code):
                self.assertTrue(400 <= status <= 599)

    def test_every_domain_error_class_uses_a_mapped_code(self) -> None:
        for cls in _all_error_classes(BunaVisionError):
            with self.subTest(cls=cls.__name__):
                self.assertIn(cls.code, STATUS_BY_CODE)

    def test_rate_limit_response_includes_retry_after(self) -> None:
        request = Request({"type": "http", "headers": [], "method": "POST", "path": "/"})
        response = asyncio.run(_domain_error(request, RateLimitedError("quota", retry_after_s=17)))
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["retry-after"], "17")


if __name__ == "__main__":
    unittest.main()
