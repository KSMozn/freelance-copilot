from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.application.dto.portfolio_dto import (
    PortfolioCreate,
    PortfolioListResponse,
    PortfolioRead,
    PortfolioUpdate,
)
from app.core.deps import CurrentUser, PortfolioServiceDep
from app.domain.exceptions import NotFoundError

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.post("", response_model=PortfolioRead, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    payload: PortfolioCreate,
    user: CurrentUser,
    service: PortfolioServiceDep,
) -> PortfolioRead:
    return await service.create(user.id, payload)


@router.get("", response_model=PortfolioListResponse)
async def list_portfolio(
    user: CurrentUser,
    service: PortfolioServiceDep,
    search: str | None = Query(default=None, max_length=200),
    domain: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PortfolioListResponse:
    return await service.list(
        user.id, search=search, domain=domain, limit=limit, offset=offset
    )


@router.get("/{portfolio_id}", response_model=PortfolioRead)
async def get_portfolio(
    portfolio_id: UUID,
    user: CurrentUser,
    service: PortfolioServiceDep,
) -> PortfolioRead:
    try:
        return await service.get(user.id, portfolio_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{portfolio_id}", response_model=PortfolioRead)
async def update_portfolio(
    portfolio_id: UUID,
    payload: PortfolioUpdate,
    user: CurrentUser,
    service: PortfolioServiceDep,
) -> PortfolioRead:
    try:
        return await service.update(user.id, portfolio_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: UUID,
    user: CurrentUser,
    service: PortfolioServiceDep,
) -> None:
    try:
        await service.delete(user.id, portfolio_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
