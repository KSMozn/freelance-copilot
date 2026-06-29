from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.ingestion import (
    CertificateEntry,
    ContentItemEntry,
    ContentType,
    CvUploadEntry,
    LinkedInSnapshotEntry,
    ParseStatus,
    UploadedFileEntry,
)
from app.infrastructure.db.models.ingestion import (
    Certificate,
    ContentItem,
    CvUpload,
    LinkedInSnapshot,
    UploadedFile,
)

# ---- to-domain converters ------------------------------------------------


def _file_to_domain(row: UploadedFile) -> UploadedFileEntry:
    return UploadedFileEntry(
        id=row.id,
        user_id=row.user_id,
        filename=row.filename,
        content_type=row.content_type,
        size_bytes=row.size_bytes,
        storage_path=row.storage_path,
        sha256=row.sha256,
        created_at=row.created_at,
    )


def _cv_to_domain(row: CvUpload) -> CvUploadEntry:
    return CvUploadEntry(
        id=row.id,
        user_id=row.user_id,
        persona_id=row.persona_id,
        filename=row.filename,
        content_type=row.content_type,
        size_bytes=row.size_bytes,
        storage_path=row.storage_path,
        sha256=row.sha256,
        extracted_text=row.extracted_text,
        parse_status=row.parse_status,  # type: ignore[arg-type]
        parse_error=row.parse_error,
        extracted_structure=dict(row.extracted_structure or {}),
        extracted_skills=list(row.extracted_skills or []),
        resume_id=row.resume_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _linkedin_to_domain(row: LinkedInSnapshot) -> LinkedInSnapshotEntry:
    return LinkedInSnapshotEntry(
        id=row.id,
        user_id=row.user_id,
        file_id=row.file_id,
        extracted_text=row.extracted_text,
        extracted_structure=dict(row.extracted_structure or {}),
        parse_status=row.parse_status,  # type: ignore[arg-type]
        parse_error=row.parse_error,
        parsed_at=row.parsed_at,
        created_at=row.created_at,
    )


def _cert_to_domain(row: Certificate) -> CertificateEntry:
    return CertificateEntry(
        id=row.id,
        user_id=row.user_id,
        name=row.name,
        issuer=row.issuer,
        issued_date=row.issued_date,
        expiry_date=row.expiry_date,
        credential_id=row.credential_id,
        credential_url=row.credential_url,
        file_id=row.file_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _content_to_domain(row: ContentItem) -> ContentItemEntry:
    return ContentItemEntry(
        id=row.id,
        user_id=row.user_id,
        type=row.type,  # type: ignore[arg-type]
        title=row.title,
        url=row.url,
        published_date=row.published_date,
        summary=row.summary,
        raw_text=row.raw_text,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


# ---- repositories --------------------------------------------------------


class SQLAlchemyUploadedFileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_sha(
        self, *, user_id: UUID, sha256: str
    ) -> UploadedFileEntry | None:
        stmt = select(UploadedFile).where(
            UploadedFile.user_id == user_id, UploadedFile.sha256 == sha256
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _file_to_domain(row) if row else None

    async def create(
        self,
        *,
        user_id: UUID,
        filename: str,
        content_type: str,
        size_bytes: int,
        storage_path: str,
        sha256: str,
    ) -> UploadedFileEntry:
        row = UploadedFile(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            sha256=sha256,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _file_to_domain(row)


class SQLAlchemyCvUploadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_sha(
        self, *, user_id: UUID, sha256: str
    ) -> CvUploadEntry | None:
        stmt = select(CvUpload).where(
            CvUpload.user_id == user_id, CvUpload.sha256 == sha256
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _cv_to_domain(row) if row else None

    async def list_for_user(self, user_id: UUID) -> list[CvUploadEntry]:
        stmt = (
            select(CvUpload)
            .where(CvUpload.user_id == user_id)
            .order_by(CvUpload.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_cv_to_domain(r) for r in rows]

    async def get(self, *, user_id: UUID, cv_id: UUID) -> CvUploadEntry | None:
        stmt = select(CvUpload).where(
            CvUpload.user_id == user_id, CvUpload.id == cv_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _cv_to_domain(row) if row else None

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
    ) -> CvUploadEntry:
        row = CvUpload(
            user_id=user_id,
            persona_id=persona_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            sha256=sha256,
            extracted_text=extracted_text,
            parse_status=parse_status,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _cv_to_domain(row)

    async def update_parse_result(
        self,
        *,
        cv_id: UUID,
        parse_status: ParseStatus,
        parse_error: str | None,
        extracted_structure: dict[str, Any] | None,
        extracted_skills: list[Any] | None,
    ) -> CvUploadEntry | None:
        row = await self._session.get(CvUpload, cv_id)
        if row is None:
            return None
        row.parse_status = parse_status
        if parse_error is not None:
            row.parse_error = parse_error
        if extracted_structure is not None:
            row.extracted_structure = extracted_structure
        if extracted_skills is not None:
            row.extracted_skills = extracted_skills
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _cv_to_domain(row)


class SQLAlchemyLinkedInSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(self, user_id: UUID) -> list[LinkedInSnapshotEntry]:
        stmt = (
            select(LinkedInSnapshot)
            .where(LinkedInSnapshot.user_id == user_id)
            .order_by(LinkedInSnapshot.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_linkedin_to_domain(r) for r in rows]

    async def get(
        self, *, user_id: UUID, snapshot_id: UUID
    ) -> LinkedInSnapshotEntry | None:
        stmt = select(LinkedInSnapshot).where(
            LinkedInSnapshot.user_id == user_id, LinkedInSnapshot.id == snapshot_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _linkedin_to_domain(row) if row else None

    async def create(
        self,
        *,
        user_id: UUID,
        file_id: UUID | None,
        extracted_text: str | None,
        parse_status: ParseStatus,
    ) -> LinkedInSnapshotEntry:
        row = LinkedInSnapshot(
            user_id=user_id,
            file_id=file_id,
            extracted_text=extracted_text,
            parse_status=parse_status,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _linkedin_to_domain(row)

    async def update_parse_result(
        self,
        *,
        snapshot_id: UUID,
        parse_status: ParseStatus,
        parse_error: str | None,
        extracted_structure: dict[str, Any] | None,
    ) -> LinkedInSnapshotEntry | None:
        row = await self._session.get(LinkedInSnapshot, snapshot_id)
        if row is None:
            return None
        row.parse_status = parse_status
        if parse_error is not None:
            row.parse_error = parse_error
        if extracted_structure is not None:
            row.extracted_structure = extracted_structure
        from datetime import UTC
        from datetime import datetime as _dt
        row.parsed_at = _dt.now(UTC)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _linkedin_to_domain(row)


class SQLAlchemyCertificateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(self, user_id: UUID) -> list[CertificateEntry]:
        stmt = (
            select(Certificate)
            .where(Certificate.user_id == user_id)
            .order_by(Certificate.issued_date.desc().nullslast(), Certificate.name)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_cert_to_domain(r) for r in rows]

    async def get(
        self, *, user_id: UUID, certificate_id: UUID
    ) -> CertificateEntry | None:
        stmt = select(Certificate).where(
            Certificate.user_id == user_id, Certificate.id == certificate_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _cert_to_domain(row) if row else None

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
    ) -> CertificateEntry:
        row = Certificate(
            user_id=user_id,
            name=name,
            issuer=issuer,
            issued_date=issued_date,
            expiry_date=expiry_date,
            credential_id=credential_id,
            credential_url=credential_url,
            file_id=file_id,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _cert_to_domain(row)

    async def update(
        self,
        *,
        user_id: UUID,
        certificate_id: UUID,
        patch: dict[str, Any],
    ) -> CertificateEntry | None:
        stmt = select(Certificate).where(
            Certificate.user_id == user_id, Certificate.id == certificate_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        for key, value in patch.items():
            if hasattr(row, key):
                setattr(row, key, value)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _cert_to_domain(row)

    async def delete(self, *, user_id: UUID, certificate_id: UUID) -> bool:
        row = await self._session.get(Certificate, certificate_id)
        if row is None or row.user_id != user_id:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True


class SQLAlchemyContentItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(self, user_id: UUID) -> list[ContentItemEntry]:
        stmt = (
            select(ContentItem)
            .where(ContentItem.user_id == user_id)
            .order_by(ContentItem.published_date.desc().nullslast(), ContentItem.title)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_content_to_domain(r) for r in rows]

    async def get(
        self, *, user_id: UUID, content_id: UUID
    ) -> ContentItemEntry | None:
        stmt = select(ContentItem).where(
            ContentItem.user_id == user_id, ContentItem.id == content_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _content_to_domain(row) if row else None

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
    ) -> ContentItemEntry:
        row = ContentItem(
            user_id=user_id,
            type=type,
            title=title,
            url=url,
            published_date=published_date,
            summary=summary,
            raw_text=raw_text,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _content_to_domain(row)

    async def update(
        self,
        *,
        user_id: UUID,
        content_id: UUID,
        patch: dict[str, Any],
    ) -> ContentItemEntry | None:
        stmt = select(ContentItem).where(
            ContentItem.user_id == user_id, ContentItem.id == content_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        for key, value in patch.items():
            if hasattr(row, key):
                setattr(row, key, value)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _content_to_domain(row)

    async def delete(self, *, user_id: UUID, content_id: UUID) -> bool:
        row = await self._session.get(ContentItem, content_id)
        if row is None or row.user_id != user_id:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True
