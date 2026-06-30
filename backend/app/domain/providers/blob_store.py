"""Outbound port for blob storage.

In dev we write to `var/uploads/` on the local filesystem; in Cloud Run
the filesystem is ephemeral so we need GCS instead. Both implementations
sit behind this protocol so the services that move bytes around
(student photo upload, CV ingestion, LinkedIn snapshots) don't have to
know which backend is in play.

`storage_path` columns in the database hold the *key* — the same value
that round-trips through `put` and `get`. For LocalBlobStore the key is
a path under `base_dir`; for GcsBlobStore it's the GCS object name.
"""
from __future__ import annotations

from typing import Protocol


class BlobStore(Protocol):
    name: str

    async def put(self, key: str, content: bytes, content_type: str) -> str:
        """Store the bytes under `key`. Returns the canonical key the
        caller should persist (callers are free to add prefixes etc.).
        """
        ...

    async def get(self, key: str) -> bytes:
        """Fetch the bytes stored under `key`. Raises FileNotFoundError
        if the key is unknown."""
        ...
