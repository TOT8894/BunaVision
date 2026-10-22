import io
import unittest

from PIL import Image

from app.domain.errors import ImageTooLargeError, InvalidImageError, UnsupportedImageFormatError
from app.services.image_validation import ImageFormat, ImageLimits, validate_image
from tests.unit.fakes import make_image

LIMITS = ImageLimits(max_bytes=10 * 1024 * 1024, max_pixels=1_000_000, min_side_px=320)


def encode(fmt: str, size: tuple[int, int] = (400, 400)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (30, 120, 60)).save(buffer, format=fmt)
    return buffer.getvalue()


class ValidateImageTests(unittest.TestCase):
    def test_accepts_jpeg_png_and_webp(self) -> None:
        for fmt in ("JPEG", "PNG", "WEBP"):
            with self.subTest(fmt=fmt):
                image = validate_image(encode(fmt), LIMITS)
                self.assertIs(image.format, ImageFormat(fmt))
                self.assertEqual((image.width, image.height), (400, 400))

    def test_empty_and_garbage_are_invalid(self) -> None:
        for data in (b"", b"definitely not an image"):
            with self.subTest(data=data[:8]), self.assertRaises(InvalidImageError):
                validate_image(data, LIMITS)

    def test_real_image_of_an_unsupported_format_is_rejected_by_content(self) -> None:
        with self.assertRaises(UnsupportedImageFormatError):
            validate_image(encode("GIF"), LIMITS)

    def test_oversized_bytes_are_rejected(self) -> None:
        small = ImageLimits(max_bytes=100, max_pixels=1_000_000, min_side_px=320)
        with self.assertRaises(ImageTooLargeError):
            validate_image(make_image(), small)

    def test_pixel_budget_is_checked_before_decoding(self) -> None:
        with self.assertRaises(InvalidImageError) as caught:
            validate_image(encode("PNG", (1200, 1200)), LIMITS)  # 1.44M px > 1M
        self.assertIn("resolution", caught.exception.public_message)

    def test_too_small_is_rejected(self) -> None:
        with self.assertRaises(InvalidImageError):
            validate_image(encode("PNG", (100, 100)), LIMITS)

    def test_truncated_jpeg_is_rejected(self) -> None:
        data = make_image()
        with self.assertRaises(InvalidImageError):
            validate_image(data[: len(data) // 2], LIMITS)


if __name__ == "__main__":
    unittest.main()
