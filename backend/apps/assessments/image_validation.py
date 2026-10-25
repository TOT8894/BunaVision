"""Server-side image validation. Pure Python plus Pillow.

The client is untrusted: a filename or MIME type proves nothing. The image is identified by
decoding its header, hard limits are checked BEFORE any pixel is decoded (so a small file cannot
expand into a huge bitmap), and only then are the pixels decoded once, because Pillow's
`verify()` accepts truncated JPEGs. It never rewrites, resizes, or re-encodes: that is the
vision service's preprocessing.
"""

import io
from dataclasses import dataclass
from enum import StrEnum

from PIL import Image, UnidentifiedImageError

from apps.common.errors import ImageTooLarge, InvalidImage, UnsupportedImageFormat

_MIB = 1024 * 1024


class ImageFormat(StrEnum):
    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WEBP"

    @property
    def content_type(self) -> str:
        return {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}[self.value]

    @property
    def extension(self) -> str:
        return {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}[self.value]


@dataclass(frozen=True, slots=True)
class ImageLimits:
    max_bytes: int
    max_pixels: int
    min_side_px: int


@dataclass(frozen=True, slots=True)
class ValidatedImage:
    data: bytes
    format: ImageFormat
    width: int
    height: int


def validate_image(data: bytes, limits: ImageLimits) -> ValidatedImage:
    """Return the image if it is a supported, readable, in-limits JPEG/PNG/WEBP."""
    if not data:
        raise InvalidImage("empty upload", public_message="The uploaded file is empty.")
    if len(data) > limits.max_bytes:
        raise ImageTooLarge(
            f"{len(data)} bytes exceeds the {limits.max_bytes} byte limit",
            public_message=f"The image is larger than the {limits.max_bytes // _MIB} MB limit.",
        )
    try:
        with Image.open(io.BytesIO(data)) as image:
            width, height = image.size
            try:
                image_format = ImageFormat(image.format)
            except ValueError:
                raise UnsupportedImageFormat(f"decoded format was {image.format!r}") from None
            if width * height > limits.max_pixels:
                raise InvalidImage(
                    f"{width}x{height} exceeds {limits.max_pixels} pixels",
                    public_message="The image resolution is too high. Please use a smaller photo.",
                )
            if min(width, height) < limits.min_side_px:
                raise InvalidImage(
                    f"{width}x{height} is below the {limits.min_side_px}px minimum side",
                    public_message=f"The image is too small. Each side must be at least {limits.min_side_px} pixels.",
                )
            image.load()  # full decode: catches truncated and corrupt pixel data
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError) as exc:
        raise InvalidImage(f"cannot decode image: {exc}") from exc
    return ValidatedImage(data=data, format=image_format, width=width, height=height)
