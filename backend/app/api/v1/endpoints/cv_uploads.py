from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.application.dto.ingestion_dto import CvUploadRead, PastedCvRequest
from app.application.services.cv_ingest_service import CvIngestService
from app.core.deps import CurrentUser, SessionDep, get_cv_ingest_service
from app.domain.entities.ingestion import CvUploadEntry
from app.infrastructure.db.repositories.sqlalchemy_ingestion_repositories import (
    SQLAlchemyCvUploadRepository,
)

router = APIRouter(prefix="/cv-uploads", tags=["ingestion"])

CvIngestDep = Annotated[CvIngestService, Depends(get_cv_ingest_service)]

# Generous cap — CVs are rarely above a couple MB; pasted text up to 200K
# chars sits well under this.
MAX_BYTES = 5 * 1024 * 1024


def _to_read(cv: CvUploadEntry) -> CvUploadRead:
    return CvUploadRead(
        id=cv.id,
        user_id=cv.user_id,
        persona_id=cv.persona_id,
        filename=cv.filename,
        content_type=cv.content_type,
        size_bytes=cv.size_bytes,
        sha256=cv.sha256,
        parse_status=cv.parse_status,
        parse_error=cv.parse_error,
        extracted_structure=cv.extracted_structure,
        extracted_skills=[s for s in (cv.extracted_skills or []) if isinstance(s, str)],
        created_at=cv.created_at,
        updated_at=cv.updated_at,
    )


@router.get("", response_model=list[CvUploadRead])
async def list_cv_uploads(
    user: CurrentUser, session: SessionDep
) -> list[CvUploadRead]:
    repo = SQLAlchemyCvUploadRepository(session)
    rows = await repo.list_for_user(user.id)
    return [_to_read(r) for r in rows]


@router.post("", response_model=CvUploadRead, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    user: CurrentUser,
    service: CvIngestDep,
    file: UploadFile = File(...),
    persona_id: UUID | None = Form(default=None),
) -> CvUploadRead:
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {MAX_BYTES // (1024 * 1024)} MB)",
        )
    result = await service.ingest(
        user_id=user.id,
        persona_id=persona_id,
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )
    return _to_read(result)


@router.post(
    "/paste", response_model=CvUploadRead, status_code=status.HTTP_201_CREATED
)
async def paste_cv(
    payload: PastedCvRequest,
    user: CurrentUser,
    service: CvIngestDep,
) -> CvUploadRead:
    """Same ingest pipeline but the body IS the text — no PDF parsing step."""
    result = await service.ingest(
        user_id=user.id,
        persona_id=payload.persona_id,
        filename=payload.title or "Pasted CV",
        content_type="text/plain",
        content=payload.text.encode("utf-8"),
    )
    return _to_read(result)
