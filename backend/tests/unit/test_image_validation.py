import unittest

from app.domain.errors import (
    ImageTooLargeError,
    InvalidImageError,
    UnsupportedImageFormatError,
)
from app.services.image_validation import ImageFormat, ImageLimits, validate_image
from tests.unit.fakes import make_image

MIB = 1024 * 1024
LIMITS = ImageLimits(max_bytes=10 * MIB, max_pixels=1_000_000, min_side_px=320)


class ValidateImageTests(unittest.TestCase):
    def test_accepts_supported_formats_and_reports_what_it_decoded(self) -> None:
        for fmt, expected in (("JPEG", ImageFormat.JPEG), ("PNG", ImageFormat.PNG), ("WEBP", ImageFormat.WEBP)):
            with self.subTest(fmt=fmt):
                image = validate_image(make_image(fmt), LIMITS)
                self.assertIs(image.format, expected)
                self.assertEqual((image.width, image.height), (400, 400))

    def test_returns_the_original_bytes_untouched(self) -> None:
        data = make_image("JPEG")
        self.assertEqual(validate_image(data, LIMITS).data, data)

    def test_rejects_empty_and_garbage(self) -> None:
        for data in (b"", b"definitely not an image"):
            with self.subTest(data=data[:10]), self.assertRaises(InvalidImageError):
                validate_image(data, LIMITS)

    def test_rejects_unsupported_formats_by_decoded_content(self) -> None:
        for fmt in ("GIF", "BMP"):
            with self.subTest(fmt=fmt), self.assertRaises(UnsupportedImageFormatError):
                validate_image(make_image(fmt), LIMITS)

    def test_rejects_oversized_uploads_before_decoding(self) -> None:
        tiny_limit = ImageLimits(max_bytes=100, max_pixels=10**9, min_side_px=1)
        with self.assertRaises(ImageTooLargeError):
            validate_image(make_image("JPEG"), tiny_limit)

    def test_rejects_images_with_too_many_pixels(self) -> None:
        limits = ImageLimits(max_bytes=10 * MIB, max_pixels=100_000, min_side_px=10)
        with self.assertRaises(InvalidImageError) as caught:
            validate_image(make_image("JPEG", (400, 400)), limits)
        self.assertIn("resolution", caught.exception.public_message)

    def test_rejects_images_that_are_too_small(self) -> None:
        with self.assertRaises(InvalidImageError) as caught:
            validate_image(make_image("PNG", (100, 100)), LIMITS)
        self.assertIn("320", caught.exception.public_message)

    def test_rejects_truncated_jpeg_which_verify_alone_would_accept(self) -> None:
        data = make_image("JPEG")
        with self.assertRaises(InvalidImageError):
            validate_image(data[: len(data) // 2], LIMITS)


if __name__ == "__main__":
    unittest.main()
