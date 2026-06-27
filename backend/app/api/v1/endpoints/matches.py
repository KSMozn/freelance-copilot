from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.application.dto.portfolio_dto import PortfolioMatchesResponse
from app.core.deps import CurrentUser, PortfolioMatchingServiceDep
from app.domain.exceptions import NotFoundError

router = APIRouter(prefix="/jobs", tags=["portfolio-matching"])


@router.post(
    "/{job_id}/match-portfolio",
    response_model=PortfolioMatchesResponse,
    status_code=status.HTTP_200_OK,
)
async def match_portfolio(
    job_id: UUID,
    user: CurrentUser,
    service: PortfolioMatchingServiceDep,
    top_n: int = Query(default=5, ge=1, le=20),
) -> PortfolioMatchesResponse:
    """Rank the user's portfolio projects against an analyzed job."""
    try:
        return await service.match(user_id=user.id, job_id=job_id, top_n=top_n)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{job_id}/portfolio-matches",
    response_model=PortfolioMatchesResponse,
)
async def get_portfolio_matches(
    job_id: UUID,
    user: CurrentUser,
    service: PortfolioMatchingServiceDep,
    top_n: int = Query(default=5, ge=1, le=20),
) -> PortfolioMatchesResponse:
    """Idempotent fetch — computes matches on demand.

    Cached embeddings make this cheap; only first-time portfolios trigger a
    provider call.
    """
    return await match_portfolio(job_id=job_id, user=user, service=service, top_n=top_n)
