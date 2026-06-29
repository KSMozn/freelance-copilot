"""Repository protocols for Phase D ingestion surfaces.

Kept together because their write patterns are mostly the same — create,
list_for_user, get_for_user. Reading: each entity is user-scoped, so
every fetch includes the user_id to enforce tenancy at the data layer.
"""
from datetime import date
from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.ingestion import (
    CertificateEntry,
    ContentItemEntry,
    ContentType,
    CvUploadEntry,
    LinkedInSnapshotEntry,
    ParseStatus,
    UploadedFileEntry,
)


class UploadedFileRepository(Protocol):
    async def get_by_sha(
        self, *, user_id: UUID, sha256: str
    ) -> UploadedFileEntry | None: ...

    async def create(
        self,
        *,
        user_id: UUID,
        filename: str,
        content_type: str,
        size_bytes: int,
        storage_path: str,
        sha256: str,
    ) -> UploadedFileEntry: ...


class CvUploadRepository(Protocol):
    async def get_by_sha(
        self, *, user_id: UUID, sha256: str
    ) -> CvUploadEntry | None: ...

    async def list_for_user(self, user_id: UUID) -> list[CvUploadEntry]: ...

    async def get(self, *, user_id: UUID, cv_id: UUID) -> CvUploadEntry | None: ...

    async def create(
        self,
        *,
        user_id: UUID,
        persona_id: UUID | None,
        filename: str,
        content_type: str,
        size_bytes: int,
        storage_path: str | None,
        sha256: str,
        extracted_text: str | None,
        parse_status: ParseStatus,
    ) -> CvUploadEntry: ...

    async def update_parse_result(
        self,
        *,
        cv_id: UUID,
        parse_status: ParseStatus,
        parse_error: str | None,
        extracted_structure: dict[str, Any] | None,
        extracted_skills: list[Any] | None,
    ) -> CvUploadEntry | None: ...


class LinkedInSnapshotRepository(Protocol):
    async def list_for_user(
        self, user_id: UUID
    ) -> list[LinkedInSnapshotEntry]: ...

    async def get(
        self, *, user_id: UUID, snapshot_id: UUID
    ) -> LinkedInSnapshotEntry | None: ...

    async def create(
        self,
        *,
        user_id: UUID,
        file_id: UUID | None,
        extracted_text: str | None,
        parse_status: ParseStatus,
    ) -> LinkedInSnapshotEntry: ...

    async def update_parse_result(
        self,
        *,
        snapshot_id: UUID,
        parse_status: ParseStatus,
        parse_error: str | None,
        extracted_structure: dict[str, Any] | None,
    ) -> LinkedInSnapshotEntry | None: ...


class CertificateRepository(Protocol):
    async def list_for_user(self, user_id: UUID) -> list[CertificateEntry]: ...

    async def get(
        self, *, user_id: UUID, certificate_id: UUID
    ) -> CertificateEntry | None: ...

    async def create(
        self,
        *,
        user_id: UUID,
        name: str,
        issuer: str,
        issued_date: date | None = None,
        expiry_date: date | None = None,
        credential_id: str | None = None,
        credential_url: str | None = None,
        file_id: UUID | None = None,
    ) -> CertificateEntry: ...

    async def update(
        self,
        *,
        user_id: UUID,
        certificate_id: UUID,
        patch: dict[str, Any],
    ) -> CertificateEntry | None: ...

    async def delete(self, *, user_id: UUID, certificate_id: UUID) -> bool: ...


class ContentItemRepository(Protocol):
    async def list_for_user(self, user_id: UUID) -> list[ContentItemEntry]: ...

    async def get(
        self, *, user_id: UUID, content_id: UUID
    ) -> ContentItemEntry | None: ...

    async def create(
        self,
        *,
        user_id: UUID,
        type: ContentType,
        title: str,
        url: str | None = None,
        published_date: date | None = None,
        summary: str | None = None,
        raw_text: str | None = None,
    ) -> ContentItemEntry: ...

    async def update(
        self,
        *,
        user_id: UUID,
        content_id: UUID,
        patch: dict[str, Any],
    ) -> ContentItemEntry | None: ...

    async def delete(self, *, user_id: UUID, content_id: UUID) -> bool: ...
