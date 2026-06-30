"""Builds the right BlobStore implementation from settings.

Dev → LocalBlobStore (writes under `var/uploads/`).
Prod (Cloud Run + GCS bucket) → GcsBlobStore.
"""
from __future__ import annotations

from pathlib import Path

from app.core.config import Settings
from app.domain.providers.blob_store import BlobStore
from app.infrastructure.storage.local_blob_store import LocalBlobStore


def build_blob_store(settings: Settings) -> BlobStore:
    if settings.blob_store == "gcs":
        # Lazy import so dev environments without the google-cloud-storage
        # package can still boot.
        from app.infrastructure.storage.gcs_blob_store import GcsBlobStore

        if not settings.gcs_uploads_bucket:
            raise RuntimeError(
                "blob_store=gcs but gcs_uploads_bucket is unset"
            )
        return GcsBlobStore(bucket_name=settings.gcs_uploads_bucket)
    return LocalBlobStore(base_dir=Path(settings.uploads_dir))
