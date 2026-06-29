from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.application.dto.repository_dto import (
    RepositoryCreate,
    RepositoryListResponse,
    RepositoryMatchesResponse,
    RepositoryRead,
)
from app.application.dto.repository_improvement_dto import (
    RepositoryImprovementsReport,
)
from app.application.services.repository_service import DuplicateRepositoryError
from app.application.services.repository_star_story_service import (
    StarStoryGenerationFailedError,
)
from app.core.deps import (
    CurrentUser,
    RepositoryImprovementServiceDep,
    RepositoryMatchingServiceDep,
    RepositoryServiceDep,
    RepositoryStarStoryServiceDep,
)
from app.domain.exceptions import NotFoundError

router = APIRouter(prefix="/repositories", tags=["repositories"])
job_repository_matches_router = APIRouter(prefix="/jobs", tags=["repositories"])


@router.post("", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED)
async def register_repository(
    payload: RepositoryCreate,
    user: CurrentUser,
    service: RepositoryServiceDep,
) -> RepositoryRead:
    try:
        return await service.create_and_scan(
            user_id=user.id,
            github_url=str(payload.github_url),
            scan_now=payload.scan_now,
        )
    except DuplicateRepositoryError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.get("/improvements", response_model=RepositoryImprovementsReport)
async def list_repository_improvements(
    user: CurrentUser,
    service: RepositoryImprovementServiceDep,
) -> RepositoryImprovementsReport:
    """Cross-job skill-gap analysis: for each scanned repo, surface the
    highest-frequency missing skills as concrete improvement suggestions.
    """
    return await service.build(user_id=user.id)


@router.get("", response_model=RepositoryListResponse)
async def list_repositories(
    user: CurrentUser,
    service: RepositoryServiceDep,
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> RepositoryListResponse:
    return await service.list(user.id, search=search, limit=limit, offset=offset)


@router.get("/{repository_id}", response_model=RepositoryRead)
async def get_repository(
    repository_id: UUID,
    user: CurrentUser,
    service: RepositoryServiceDep,
) -> RepositoryRead:
    try:
        return await service.get(user.id, repository_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{repository_id}/rescan", response_model=RepositoryRead)
async def rescan_repository(
    repository_id: UUID,
    user: CurrentUser,
    service: RepositoryServiceDep,
) -> RepositoryRead:
    try:
        return await service.rescan(user.id, repository_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{repository_id}/star-story", response_model=RepositoryRead)
async def generate_star_story(
    repository_id: UUID,
    user: CurrentUser,
    service: RepositoryStarStoryServiceDep,
) -> RepositoryRead:
    try:
        return await service.generate(user_id=user.id, repository_id=repository_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except StarStoryGenerationFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repository_id: UUID,
    user: CurrentUser,
    service: RepositoryServiceDep,
) -> None:
    try:
        await service.delete(user.id, repository_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@job_repository_matches_router.post(
    "/{job_id}/match-repositories", response_model=RepositoryMatchesResponse
)
async def match_repositories(
    job_id: UUID,
    user: CurrentUser,
    service: RepositoryMatchingServiceDep,
    top_n: int = Query(default=5, ge=1, le=20),
) -> RepositoryMatchesResponse:
    try:
        return await service.match(user_id=user.id, job_id=job_id, top_n=top_n)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
