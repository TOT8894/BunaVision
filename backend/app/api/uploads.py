"""Reading an upload into memory with a hard ceiling."""

from fastapi import UploadFile

from app.domain.errors import ImageTooLargeError


async def read_upload(upload: UploadFile, max_bytes: int) -> bytes:
    """Read at most `max_bytes` + 1 bytes, so an oversized file is detected without loading it all.

    The request-size middleware already bounds the whole body; this is the second layer that
    ties the limit to the image itself.
    """
    data = await upload.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ImageTooLargeError(
            f"upload exceeds {max_bytes} bytes",
            public_message="The image is larger than the allowed size.",
        )
    return data
