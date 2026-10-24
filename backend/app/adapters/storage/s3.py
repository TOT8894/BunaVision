"""Amazon S3 implementation of the `ImageStore` port.

Buckets must be private. Images are served through short-lived presigned URLs created at
response time, so no public URL is ever stored. boto3 is synchronous, so every call runs in a
worker thread to keep the event loop free (presigning can also touch the credential chain).

Credentials come from the default AWS chain (IAM role in production). Nothing is configured
here. The task role needs only s3:PutObject, s3:GetObject and s3:DeleteObject on the bucket.
"""

import asyncio
from collections.abc import Sequence
from typing import Any, Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.domain.errors import PersistenceError

_DELETE_BATCH = 1000  # S3's per-request limit for delete_objects


class S3Api(Protocol):
    """The slice of the boto3 S3 client this adapter uses."""

    def put_object(self, **kwargs: Any) -> Any: ...
    def delete_objects(self, **kwargs: Any) -> Any: ...
    def generate_presigned_url(self, ClientMethod: str, **kwargs: Any) -> str: ...  # noqa: N803


def create_s3_client(*, region: str, endpoint_url: str | None) -> S3Api:
    client: S3Api = boto3.client(
        "s3",
        region_name=region,
        endpoint_url=endpoint_url,
        config=Config(signature_version="s3v4"),
    )
    return client


class S3ImageStore:
    def __init__(self, *, client: S3Api, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        try:
            await asyncio.to_thread(
                self._client.put_object,
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        except (ClientError, BotoCoreError) as exc:
            raise PersistenceError(f"S3 put failed for {key}: {exc}") from exc

    async def url_for(self, key: str, ttl_s: int) -> str:
        try:
            return await asyncio.to_thread(
                self._client.generate_presigned_url,
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=ttl_s,
            )
        except (ClientError, BotoCoreError) as exc:
            raise PersistenceError(f"S3 presign failed for {key}: {exc}") from exc

    async def delete(self, keys: Sequence[str]) -> None:
        for start in range(0, len(keys), _DELETE_BATCH):
            batch = keys[start : start + _DELETE_BATCH]
            try:
                response = await asyncio.to_thread(
                    self._client.delete_objects,
                    Bucket=self._bucket,
                    Delete={"Objects": [{"Key": key} for key in batch], "Quiet": True},
                )
            except (ClientError, BotoCoreError) as exc:
                raise PersistenceError(f"S3 delete failed: {exc}") from exc
            errors = response.get("Errors")
            if errors:
                raise PersistenceError(f"S3 could not delete {len(errors)} object(s): {errors[:3]}")
