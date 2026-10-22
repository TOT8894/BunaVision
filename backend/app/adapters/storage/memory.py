"""In-memory `ImageStore`. Development and tests only: nothing survives a restart, and the
URLs it returns cannot be fetched by a browser. Use S3 for anything real."""

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

    def keys(self) -> set[str]:
        """Test helper: which objects are currently stored."""
        return set(self._objects)
