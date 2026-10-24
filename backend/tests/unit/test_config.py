import unittest

from pydantic import ValidationError

from app.core.config import Settings


_REQUIRED = {
    "vision_service_url": "http://vision:9000",
    "gemini_api_key": "test-api-key",
    "gemini_model": "test-model",
    "image_store": "memory",
    "database_url": "postgresql+asyncpg://user:pass@localhost/testdb",
    "jwt_secret": "x" * 32,
}


class RequiredConfigurationTests(unittest.TestCase):
    def test_empty_gemini_api_key_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(**(_REQUIRED | {"gemini_api_key": "   "}))

    def test_whitespace_gemini_model_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(**(_REQUIRED | {"gemini_model": "   "}))

    def test_empty_database_url_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(**(_REQUIRED | {"database_url": "   "}))

    def test_database_url_without_database_name_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(**(_REQUIRED | {"database_url": "postgresql+asyncpg://user:pass@localhost"}))
