"""Server-side image validation.

The client is untrusted: a filename or MIME type proves nothing. This module identifies the
image by decoding its header and checks hard limits BEFORE any pixel data is decoded, so a
small compressed file cannot expand into a huge bitmap (decompression bomb). Only after those
limits pass does it decode the pixels once, because `verify()` alone accepts truncated JPEGs.

It validates only. It never rewrites, resizes, or re-encodes: orientation and resizing are
preprocessing, which belongs to the vision service.
"""

import io
from dataclasses import dataclass
from enum import StrEnum

from PIL import Image, UnidentifiedImageError

from app.domain.errors import ImageTooLargeError, InvalidImageError, UnsupportedImageFormatError

_MIB = 1024 * 1024


class ImageFormat(StrEnum):
    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WEBP"

    @property
    def content_type(self) -> str:
        return _CONTENT_TYPES[self]

    @property
    def extension(self) -> str:
        return _EXTENSIONS[self]


_CONTENT_TYPES = {
    ImageFormat.JPEG: "image/jpeg",
    ImageFormat.PNG: "image/png",
    ImageFormat.WEBP: "image/webp",
}
_EXTENSIONS = {ImageFormat.JPEG: "jpg", ImageFormat.PNG: "png", ImageFormat.WEBP: "webp"}


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
    """Return the image if it is a supported, readable, in-limits JPEG/PNG/WEBP.

    Raises a `ClientInputError` subclass otherwise. CPU-bound: call from a worker thread.
    Peak memory while decoding is bounded by `limits.max_pixels`.
    """
    if not data:
        raise InvalidImageError("empty upload", public_message="The uploaded file is empty.")
    if len(data) > limits.max_bytes:
        raise ImageTooLargeError(
            f"{len(data)} bytes exceeds the {limits.max_bytes} byte limit",
            public_message=f"The image is larger than the {limits.max_bytes // _MIB} MB limit.",
        )

    try:
        with Image.open(io.BytesIO(data)) as image:
            width, height = image.size
            try:
                image_format = ImageFormat(image.format)
            except ValueError:
                raise UnsupportedImageFormatError(f"decoded format was {image.format!r}") from None
            if width * height > limits.max_pixels:
                raise InvalidImageError(
                    f"{width}x{height} exceeds {limits.max_pixels} pixels",
                    public_message="The image resolution is too high. Please use a smaller photo.",
                )
            if min(width, height) < limits.min_side_px:
                raise InvalidImageError(
                    f"{width}x{height} is below the {limits.min_side_px}px minimum side",
                    public_message=(
                        f"The image is too small. Each side must be at least "
                        f"{limits.min_side_px} pixels."
                    ),
                )
            image.load()  # full decode: catches truncated and corrupt pixel data
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
        Image.DecompressionBombError,
    ) as exc:
        raise InvalidImageError(f"cannot decode image: {exc}") from exc

    return ValidatedImage(data=data, format=image_format, width=width, height=height)
