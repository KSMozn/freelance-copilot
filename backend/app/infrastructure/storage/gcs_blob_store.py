"""GcsBlobStore — Google Cloud Storage-backed blob store for prod.

`google-cloud-storage` is a sync client; we offload to a thread so we
don't block the FastAPI event loop. Authentication uses the Cloud Run
runtime service account (Application Default Credentials), so no key
material lives in the container.
"""
from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


class GcsBlobStore:
    name = "gcs"

    def __init__(self, bucket_name: str) -> None:
        from google.cloud import storage  # imported lazily so dev doesn't need the dep

        self._bucket_name = bucket_name
        self._client = storage.Client()
        self._bucket = self._client.bucket(bucket_name)

    async def put(self, key: str, content: bytes, content_type: str) -> str:
        blob = self._bucket.blob(key)
        await asyncio.to_thread(blob.upload_from_string, content, content_type=content_type)
        return key

    async def get(self, key: str) -> bytes:
        blob = self._bucket.blob(key)
        if not await asyncio.to_thread(blob.exists):
            raise FileNotFoundError(key)
        return await asyncio.to_thread(blob.download_as_bytes)
