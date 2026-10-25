"""In-memory image store.

DEVELOPMENT AND TESTS ONLY. Images are lost on restart and the URLs it returns use a
`memory://` scheme that no browser can fetch. Use S3 (or an S3-compatible store such as MinIO
via S3_ENDPOINT_URL) to see real images.
"""

from collections.abc import Sequence


class InMemoryImageStore:
    def __init__(self) -> None:
        self._objects: dict[str, tuple[bytes, str]] = {}

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        self._objects[key] = (data, content_type)

    async def url_for(self, key: str, ttl_s: int) -> str:
        return f"memory://{key}?ttl={ttl_s}"

    async def delete(self, keys: Sequence[str]) -> None:
        for key in keys:
            self._objects.pop(key, None)

    # --- Inspection helpers for tests -----------------------------------------------------

    def keys(self) -> set[str]:
        return set(self._objects)

    def get(self, key: str) -> tuple[bytes, str]:
        return self._objects[key]
