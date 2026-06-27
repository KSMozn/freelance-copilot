from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.application.dto.job_dto import (
    JobCreate,
    JobListResponse,
    JobRead,
    JobUpdate,
)
from app.core.deps import CurrentUser, JobServiceDep
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


@router.get("", response_model=JobListResponse)
async def list_jobs(
    user: CurrentUser,
    service: JobServiceDep,
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> JobListResponse:
    return await service.list(
        user.id, status=status_filter, limit=limit, offset=offset, search=search
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
