from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.application.dto.resume_dto import (
    ResumeCreate,
    ResumeListResponse,
    ResumeRead,
    ResumeUpdate,
)
from app.core.deps import CurrentUser, ResumeServiceDep
from app.domain.exceptions import NotFoundError

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def create_resume(
    payload: ResumeCreate,
    user: CurrentUser,
    service: ResumeServiceDep,
) -> ResumeRead:
    return await service.create(user.id, payload)


@router.get("", response_model=ResumeListResponse)
async def list_resumes(
    user: CurrentUser,
    service: ResumeServiceDep,
    search: str | None = Query(default=None, max_length=200),
    domain: str | None = Query(default=None, max_length=120),
    skill: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ResumeListResponse:
    return await service.list(
        user.id,
        search=search,
        domain=domain,
        skill=skill,
        limit=limit,
        offset=offset,
    )


@router.get("/{resume_id}", response_model=ResumeRead)
async def get_resume(
    resume_id: UUID,
    user: CurrentUser,
    service: ResumeServiceDep,
) -> ResumeRead:
    try:
        return await service.get(user.id, resume_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{resume_id}", response_model=ResumeRead)
async def update_resume(
    resume_id: UUID,
    payload: ResumeUpdate,
    user: CurrentUser,
    service: ResumeServiceDep,
) -> ResumeRead:
    try:
        return await service.update(user.id, resume_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: UUID,
    user: CurrentUser,
    service: ResumeServiceDep,
) -> None:
    try:
        await service.delete(user.id, resume_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
