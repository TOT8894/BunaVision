import unittest

from pydantic import ValidationError

from app.core.config import AssessmentStoreBackend, ImageStoreBackend, Settings

REQUIRED = {
    "vision_service_url": "http://vision:9000",
    "gemini_api_key": "secret",
    "gemini_model": "some-model",
    "image_store": "memory",
    "assessment_store": "memory",
}


def make(**overrides: object) -> Settings:
    return Settings(_env_file=None, **{**REQUIRED, **overrides})  # type: ignore[arg-type]


class SettingsTests(unittest.TestCase):
    def test_valid_settings_load_with_documented_defaults(self) -> None:
        settings = make()
        self.assertIs(settings.image_store, ImageStoreBackend.MEMORY)
        self.assertIs(settings.assessment_store, AssessmentStoreBackend.MEMORY)
        self.assertEqual(settings.cors_allowed_origins, [])
        self.assertGreater(settings.max_body_bytes, settings.max_image_bytes)

    def test_each_required_value_has_no_default(self) -> None:
        for name in REQUIRED:
            with self.subTest(missing=name), self.assertRaises(ValidationError):
                Settings(_env_file=None, **{k: v for k, v in REQUIRED.items() if k != name})  # type: ignore[arg-type]

    def test_secret_is_not_printed(self) -> None:
        self.assertNotIn("secret", repr(make()))

    def test_wildcard_cors_is_rejected_and_lists_are_split(self) -> None:
        with self.assertRaises(ValidationError):
            make(cors_allowed_origins="*")
        settings = make(cors_allowed_origins="https://a.example, https://b.example")
        self.assertEqual(settings.cors_allowed_origins, ["https://a.example", "https://b.example"])

    def test_s3_requires_bucket_and_region(self) -> None:
        with self.assertRaises(ValidationError):
            make(image_store="s3")
        ok = make(image_store="s3", s3_bucket="b", s3_region="eu-west-1")
        self.assertEqual(ok.s3_bucket, "b")

    def test_ranges_are_validated(self) -> None:
        for field, value in (("max_image_bytes", 0), ("gemini_temperature", 3), ("image_url_ttl_s", 10**9)):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                make(**{field: value})


if __name__ == "__main__":
    unittest.main()
