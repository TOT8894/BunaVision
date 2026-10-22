import unittest
from typing import Any

from botocore.exceptions import ClientError

from app.adapters.storage.s3 import S3ImageStore
from app.domain.errors import PersistenceError


class FakeS3:
    def __init__(self, *, fail: bool = False, delete_errors: list[dict] | None = None) -> None:
        self.puts: list[dict[str, Any]] = []
        self.delete_batches: list[list[str]] = []
        self._fail = fail
        self._delete_errors = delete_errors

    def _maybe_fail(self) -> None:
        if self._fail:
            raise ClientError({"Error": {"Code": "AccessDenied", "Message": "no"}}, "op")

    def put_object(self, **kwargs: Any) -> None:
        self._maybe_fail()
        self.puts.append(kwargs)

    def delete_objects(self, **kwargs: Any) -> dict[str, Any]:
        self._maybe_fail()
        self.delete_batches.append([o["Key"] for o in kwargs["Delete"]["Objects"]])
        return {"Errors": self._delete_errors} if self._delete_errors else {}

    def generate_presigned_url(self, ClientMethod: str, **kwargs: Any) -> str:  # noqa: N803
        self._maybe_fail()
        return f"https://signed.example/{kwargs['Params']['Key']}?exp={kwargs['ExpiresIn']}"


class S3StoreTests(unittest.IsolatedAsyncioTestCase):
    async def test_put_sets_bucket_key_and_content_type(self) -> None:
        s3 = FakeS3()
        await S3ImageStore(client=s3, bucket="b").put("k", b"data", "image/png")
        self.assertEqual(s3.puts, [{"Bucket": "b", "Key": "k", "Body": b"data", "ContentType": "image/png"}])

    async def test_url_is_presigned_with_the_ttl(self) -> None:
        url = await S3ImageStore(client=FakeS3(), bucket="b").url_for("a/b.jpg", 900)
        self.assertEqual(url, "https://signed.example/a/b.jpg?exp=900")

    async def test_delete_is_batched_at_the_s3_limit(self) -> None:
        s3 = FakeS3()
        await S3ImageStore(client=s3, bucket="b").delete([f"k{i}" for i in range(2500)])
        self.assertEqual([len(b) for b in s3.delete_batches], [1000, 1000, 500])

    async def test_failures_become_persistence_errors(self) -> None:
        store = S3ImageStore(client=FakeS3(fail=True), bucket="b")
        with self.assertRaises(PersistenceError):
            await store.put("k", b"x", "image/png")
        with self.assertRaises(PersistenceError):
            await store.url_for("k", 60)
        with self.assertRaises(PersistenceError):
            await store.delete(["k"])

    async def test_partial_delete_failures_are_not_swallowed(self) -> None:
        store = S3ImageStore(client=FakeS3(delete_errors=[{"Key": "k", "Code": "x"}]), bucket="b")
        with self.assertRaises(PersistenceError):
            await store.delete(["k"])


if __name__ == "__main__":
    unittest.main()
