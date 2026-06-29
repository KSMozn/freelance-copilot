from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.application.dto.ingestion_dto import LinkedInSnapshotRead
from app.application.services.linkedin_ingest_service import LinkedInIngestService
from app.core.deps import CurrentUser, SessionDep, get_linkedin_ingest_service
from app.domain.entities.ingestion import LinkedInSnapshotEntry
from app.infrastructure.db.repositories.sqlalchemy_ingestion_repositories import (
    SQLAlchemyLinkedInSnapshotRepository,
)

router = APIRouter(prefix="/linkedin", tags=["ingestion"])

LinkedInDep = Annotated[LinkedInIngestService, Depends(get_linkedin_ingest_service)]

MAX_BYTES = 5 * 1024 * 1024


def _to_read(s: LinkedInSnapshotEntry) -> LinkedInSnapshotRead:
    return LinkedInSnapshotRead(
        id=s.id,
        user_id=s.user_id,
        parse_status=s.parse_status,
        parse_error=s.parse_error,
        extracted_structure=s.extracted_structure,
        parsed_at=s.parsed_at,
        created_at=s.created_at,
    )


@router.get("", response_model=list[LinkedInSnapshotRead])
async def list_snapshots(
    user: CurrentUser, session: SessionDep
) -> list[LinkedInSnapshotRead]:
    repo = SQLAlchemyLinkedInSnapshotRepository(session)
    rows = await repo.list_for_user(user.id)
    return [_to_read(r) for r in rows]


@router.post("/import", response_model=LinkedInSnapshotRead, status_code=status.HTTP_201_CREATED)
async def import_linkedin(
    user: CurrentUser,
    service: LinkedInDep,
    file: UploadFile = File(...),
) -> LinkedInSnapshotRead:
    """Accept a LinkedIn 'Save to PDF' export and ingest into the graph."""
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {MAX_BYTES // (1024 * 1024)} MB)",
        )
    result = await service.ingest(
        user_id=user.id,
        filename=file.filename or "linkedin.pdf",
        content_type=file.content_type or "application/pdf",
        content=content,
    )
    return _to_read(result)
