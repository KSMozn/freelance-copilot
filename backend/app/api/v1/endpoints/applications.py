from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.application.dto.application_dto import (
    ApplicationDetailsUpdate,
    ApplicationHistoryRead,
    ApplicationListResponse,
    ApplicationRead,
    CreateFromProposalRequest,
    StatusUpdateRequest,
)
from app.core.deps import ApplicationServiceDep, CurrentUser
from app.domain.entities.application import ApplicationStatus
from app.domain.exceptions import AlreadyExistsError, NotFoundError
from app.domain.services.application_state_machine import InvalidTransitionError

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post(
    "/from-proposal/{proposal_id}",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_from_proposal(
    proposal_id: UUID,
    user: CurrentUser,
    service: ApplicationServiceDep,
    payload: CreateFromProposalRequest | None = None,
) -> ApplicationRead:
    """Turn a generated proposal into an application, snapshotting context."""
    body = payload or CreateFromProposalRequest()
    try:
        return await service.create_from_proposal(
            user_id=user.id, proposal_id=proposal_id, payload=body
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=ApplicationListResponse)
async def list_applications(
    user: CurrentUser,
    service: ApplicationServiceDep,
    status_filter: ApplicationStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApplicationListResponse:
    return await service.list(
        user_id=user.id,
        status=status_filter,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(
    application_id: UUID,
    user: CurrentUser,
    service: ApplicationServiceDep,
) -> ApplicationRead:
    try:
        return await service.get(user_id=user.id, application_id=application_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{application_id}/status", response_model=ApplicationRead)
async def update_application_status(
    application_id: UUID,
    payload: StatusUpdateRequest,
    user: CurrentUser,
    service: ApplicationServiceDep,
) -> ApplicationRead:
    try:
        return await service.update_status(
            user_id=user.id, application_id=application_id, payload=payload
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.patch("/{application_id}", response_model=ApplicationRead)
async def update_application_details(
    application_id: UUID,
    payload: ApplicationDetailsUpdate,
    user: CurrentUser,
    service: ApplicationServiceDep,
) -> ApplicationRead:
    try:
        return await service.update_details(
            user_id=user.id, application_id=application_id, payload=payload
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{application_id}/history",
    response_model=list[ApplicationHistoryRead],
)
async def get_application_history(
    application_id: UUID,
    user: CurrentUser,
    service: ApplicationServiceDep,
) -> list[ApplicationHistoryRead]:
    try:
        return await service.get_history(
            user_id=user.id, application_id=application_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_application(
    application_id: UUID,
    user: CurrentUser,
    service: ApplicationServiceDep,
) -> None:
    try:
        await service.delete(user_id=user.id, application_id=application_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
