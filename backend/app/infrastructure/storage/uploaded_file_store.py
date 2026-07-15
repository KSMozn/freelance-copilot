"""Shared helper for persisting a user upload into the `uploaded_files`
registry + the blob store.

Both profile photos and feedback screenshots follow the same shape: hash
the bytes, dedup by ``(user_id, sha256)``, write the blob under a stable
sha-based key, and record an ``UploadedFile`` row. This centralises that
logic so new upload surfaces don't re-implement (and drift from) it.

Returns the ``UploadedFile`` row (flushed, id populated). The caller owns
the commit and stamps the returned id onto whatever domain row references
it.
"""
from __future__ import annotations

import hashlib
import logging
import re
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.providers.blob_store import BlobStore
from app.infrastructure.db.models.ingestion import UploadedFile

logger = logging.getLogger(__name__)

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: str, *, fallback: str = "upload") -> str:
    """Strip path components and unsafe chars from an attacker-controlled
    client filename so it can never traverse out of its blob prefix."""
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    cleaned = _UNSAFE.sub("_", base).strip("._")
    return cleaned or fallback


async def store_uploaded_file(
    session: AsyncSession,
    blobs: BlobStore,
    *,
    user_id: UUID,
    prefix: str,
    filename: str,
    content_type: str,
    content: bytes,
) -> UploadedFile:
    """Persist ``content`` and return its ``UploadedFile`` row.

    ``prefix`` is the blob-key namespace (e.g. ``"feedback-screenshots"``).
    Dedups by ``(user_id, sha256)``; on a dedup hit whose blob has gone
    missing (ephemeral FS on Cloud Run), the blob is re-written under the
    canonical key. Blob-write failures degrade gracefully — the registry
    row is still created so the reference is never dangling.
    """
    sha = hashlib.sha256(content).hexdigest()
    key = f"{prefix}/{sha}-{safe_filename(filename)}"

    existing = await session.execute(
        select(UploadedFile).where(
            UploadedFile.user_id == user_id, UploadedFile.sha256 == sha
        )
    )
    file_row = existing.scalar_one_or_none()

    if file_row is None:
        try:
            storage_path = await blobs.put(key, content, content_type)
        except Exception as exc:  
            logger.warning("Failed to write upload %s: %s", key, exc)
            storage_path = key
        file_row = UploadedFile(
            id=uuid4(),
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            size_bytes=len(content),
            storage_path=storage_path,
            sha256=sha,
        )
        session.add(file_row)
        await session.flush()
        return file_row

    # Dedup hit: re-write the blob if it went missing under us.
    try:
        await blobs.get(file_row.storage_path)
    except (FileNotFoundError, OSError):
        try:
            file_row.storage_path = await blobs.put(key, content, content_type)
            await session.flush()
        except Exception as exc:  # best-effort
            logger.warning("Failed to refresh stale blob %s: %s", key, exc)
    return file_row
