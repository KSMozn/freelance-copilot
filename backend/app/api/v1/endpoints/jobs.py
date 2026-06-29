from typing import Literal
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

JobSortBy = Literal[
    "created_at",
    "title",
    "score",
    "score.technical_fit",
    "score.domain_fit",
    "score.proposal_count",
    "score.budget_attractiveness",
    "score.client_quality",
    "score.estimated_effort",
    "score.risk_level",
    "score.strategic_value",
]
JobSortDir = Literal["asc", "desc"]

from app.application.dto.job_dto import (
    JobCreate,
    JobListResponse,
    JobRead,
    JobUpdate,
)
from app.application.dto.job_import_dto import JobImportResponse
from app.application.services.job_import_service import (
    InvalidImageError,
    JobImportFailedError,
)
from app.core.deps import CurrentUser, JobImportServiceDep, JobServiceDep
from app.domain.entities.job import JobStatus
from app.domain.exceptions import NotFoundError

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    user: CurrentUser,
    service: JobServiceDep,
) -> JobRead:
    return await service.create(user.id, payload)


@router.post(
    "/import-image",
    response_model=JobImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_job_from_image(
    user: CurrentUser,
    service: JobImportServiceDep,
    image: UploadFile = File(..., description="Upwork screenshot (PNG / JPEG / WebP, ≤10MB)"),
    source_url: str | None = Form(default=None),
) -> JobImportResponse:
    """Extract a job post from a screenshot and persist it.

    Uses the configured multimodal AI provider. With `AI_PROVIDER=mock`, the
    extraction returns a clearly-labeled placeholder — set OPENAI/CLAUDE
    credentials for real extraction.
    """
    contents = await image.read()
    mime_type = image.content_type or "application/octet-stream"
    try:
        return await service.import_from_image(
            user_id=user.id,
            image_bytes=contents,
            image_mime_type=mime_type,
            source_url=source_url,
        )
    except InvalidImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except JobImportFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc


@router.get("", response_model=JobListResponse)
async def list_jobs(
    user: CurrentUser,
    service: JobServiceDep,
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: JobSortBy = Query(default="created_at"),
    sort_dir: JobSortDir = Query(default="desc"),
) -> JobListResponse:
    return await service.list(
        user.id,
        status=status_filter,
        limit=limit,
        offset=offset,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: UUID,
    user: CurrentUser,
    service: JobServiceDep,
) -> JobRead:
    try:
        return await service.get(user.id, job_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{job_id}", response_model=JobRead)
async def update_job(
    job_id: UUID,
    payload: JobUpdate,
    user: CurrentUser,
    service: JobServiceDep,
) -> JobRead:
    try:
        return await service.update(user.id, job_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    user: CurrentUser,
    service: JobServiceDep,
) -> None:
    try:
        await service.delete(user.id, job_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
