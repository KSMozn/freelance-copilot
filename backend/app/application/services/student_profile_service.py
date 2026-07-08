"""StudentProfileService — wizard CRUD over student_profiles + entries.

The service speaks directly to SQLAlchemy because the student surface is
small and self-contained (two tables, no cross-cutting reads). Keeping a
separate repository layer would be ceremony without benefit.

Behaviours:
  * `get_profile` returns the row if it exists, None otherwise.
  * `upsert_profile` accepts a partial payload (`StudentProfileUpdate`)
    and creates or updates accordingly. Only sent fields touch the row;
    unsent fields keep their stored value. `mark_steps` appends to
    `completed_steps` (set semantics).
  * `attach_photo` ingests bytes into `uploaded_files` (dedup by sha256)
    and stamps the file_id onto the profile.
  * Entries: list / create / update / delete. Listing groups by `kind`
    and orders by `(sort_order, created_at)` for stable wizard rendering.
"""
from __future__ import annotations

import hashlib
import logging
import re
from pathlib import PurePosixPath
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.student_dto import (
    StudentEntryUpsert,
    StudentProfileUpdate,
)
from app.domain.providers.blob_store import BlobStore
from app.infrastructure.db.models.ingestion import UploadedFile
from app.infrastructure.db.models.student_profile import (
    StudentProfile,
    StudentProfileEntry,
)

logger = logging.getLogger(__name__)

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_filename(filename: str) -> str:
    """Reduce a client-supplied filename to a single safe path component.

    Drops directory components (`../`, absolute paths, backslashes) and any
    character outside `[A-Za-z0-9._-]`, then trims leading dots so the result
    can never traverse out of the storage prefix. Falls back to `photo`.
    """
    base = PurePosixPath(filename.replace("\\", "/")).name
    cleaned = _UNSAFE_FILENAME_CHARS.sub("_", base).lstrip(".")
    return cleaned or "photo"


class StudentProfileService:
    def __init__(
        self,
        session: AsyncSession,
        blob_store: BlobStore,
    ) -> None:
        self._session = session
        self._blobs = blob_store

    # ---- profile ------------------------------------------------------

    async def get_profile(self, user_id: UUID) -> StudentProfile | None:
        return await self._session.get(StudentProfile, user_id)

    async def upsert_profile(
        self,
        user_id: UUID,
        payload: StudentProfileUpdate,
    ) -> StudentProfile:
        row = await self._session.get(StudentProfile, user_id)
        if row is None:
            row = StudentProfile(user_id=user_id)
            self._session.add(row)

        # Apply only sent fields. `model_dump(exclude_unset=True)` is the
        # standard pydantic v2 idiom for "what the client actually sent."
        data = payload.model_dump(exclude_unset=True)

        mark_steps: list[str] | None = data.pop("mark_steps", None)
        links = data.pop("links", None)

        for key, value in data.items():
            setattr(row, key, value)

        if links is not None:
            # links comes through as a dict already because of pydantic v2's
            # model_dump on nested BaseModel.
            existing = dict(row.links or {})
            existing.update({k: v for k, v in links.items() if v is not None})
            row.links = existing

        if mark_steps:
            existing_steps = list(row.completed_steps or [])
            for step in mark_steps:
                if step not in existing_steps:
                    existing_steps.append(step)
            row.completed_steps = existing_steps

        await self._session.commit()
        await self._session.refresh(row)
        return row

    # ---- photo --------------------------------------------------------

    async def attach_photo(
        self,
        *,
        user_id: UUID,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> tuple[StudentProfile, UploadedFile]:
        """Store the photo in the uploaded_files registry (dedup by sha)
        and stamp the file_id on the profile. Returns both.
        """
        sha = hashlib.sha256(content).hexdigest()

        # Dedup by (user_id, sha256).
        existing = await self._session.execute(
            select(UploadedFile).where(
                UploadedFile.user_id == user_id, UploadedFile.sha256 == sha
            )
        )
        file_row = existing.scalar_one_or_none()

        # Key shape: `student-photos/<sha>-<original-filename>`. Stable
        # across re-uploads (sha-based) and human-readable in logs. The raw
        # client filename is attacker-controlled — strip any path components
        # and unsafe chars so it can never traverse out of the blob prefix.
        key = f"student-photos/{sha}-{_safe_filename(filename)}"

        if file_row is None:
            try:
                storage_path = await self._blobs.put(key, content, content_type)
            except Exception as exc:
                logger.warning("Failed to write student photo: %s", exc)
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
            self._session.add(file_row)
            await self._session.flush()
        else:
            # Dedup hit: same user + sha. Resilience for migrations (the
            # stored path may have changed shape, or the blob may be gone
            # — e.g. ephemeral filesystem on Cloud Run after a redeploy).
            # Re-PUT under the canonical key and refresh storage_path.
            try:
                await self._blobs.get(file_row.storage_path)
            except (FileNotFoundError, OSError):
                try:
                    file_row.storage_path = await self._blobs.put(
                        key, content, content_type
                    )
                    await self._session.flush()
                except Exception as exc:  # best-effort
                    logger.warning("Failed to refresh stale photo blob: %s", exc)

        profile = await self._session.get(StudentProfile, user_id)
        if profile is None:
            profile = StudentProfile(user_id=user_id)
            self._session.add(profile)
        profile.photo_file_id = file_row.id

        await self._session.commit()
        await self._session.refresh(profile)
        return profile, file_row

    async def get_photo(self, user_id: UUID) -> tuple[UploadedFile, bytes] | None:
        profile = await self._session.get(StudentProfile, user_id)
        if profile is None or profile.photo_file_id is None:
            return None
        file_row = await self._session.get(UploadedFile, profile.photo_file_id)
        if file_row is None:
            return None
        try:
            data = await self._blobs.get(file_row.storage_path)
        except (FileNotFoundError, OSError) as exc:
            logger.warning("Failed to read student photo: %s", exc)
            return None
        return file_row, data

    # ---- entries ------------------------------------------------------

    async def list_entries(self, user_id: UUID) -> list[StudentProfileEntry]:
        stmt = (
            select(StudentProfileEntry)
            .where(StudentProfileEntry.user_id == user_id)
            .order_by(
                StudentProfileEntry.kind,
                StudentProfileEntry.sort_order,
                StudentProfileEntry.created_at,
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return list(rows)

    async def create_entry(
        self, user_id: UUID, payload: StudentEntryUpsert
    ) -> StudentProfileEntry:
        row = StudentProfileEntry(
            id=uuid4(),
            user_id=user_id,
            kind=payload.kind,
            title=payload.title,
            organization=payload.organization,
            start_date=payload.start_date,
            end_date=payload.end_date,
            is_current=payload.is_current,
            description=payload.description,
            url=payload.url,
            details=dict(payload.details),
            sort_order=payload.sort_order,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def update_entry(
        self,
        user_id: UUID,
        entry_id: UUID,
        payload: StudentEntryUpsert,
    ) -> StudentProfileEntry | None:
        row = await self._session.get(StudentProfileEntry, entry_id)
        if row is None or row.user_id != user_id:
            return None
        row.kind = payload.kind
        row.title = payload.title
        row.organization = payload.organization
        row.start_date = payload.start_date
        row.end_date = payload.end_date
        row.is_current = payload.is_current
        row.description = payload.description
        row.url = payload.url
        row.details = dict(payload.details)
        row.sort_order = payload.sort_order
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def delete_entry(self, user_id: UUID, entry_id: UUID) -> bool:
        row = await self._session.get(StudentProfileEntry, entry_id)
        if row is None or row.user_id != user_id:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True

    # ---- aggregate read for CV renderer -------------------------------

    async def load_profile_bundle(
        self, user_id: UUID
    ) -> tuple[StudentProfile | None, list[StudentProfileEntry]]:
        profile = await self.get_profile(user_id)
        entries = await self.list_entries(user_id)
        return profile, entries

    @staticmethod
    def group_entries(
        entries: list[StudentProfileEntry],
    ) -> dict[str, list[StudentProfileEntry]]:
        """Group entries by kind for the CV renderer to draw sections."""
        grouped: dict[str, list[Any]] = {}
        for e in entries:
            grouped.setdefault(e.kind, []).append(e)
        return grouped
