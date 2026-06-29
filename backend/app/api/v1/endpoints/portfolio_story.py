from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from app.application.dto.portfolio_story_dto import PortfolioStoryRead
from app.application.services.portfolio_story_service import (
    PortfolioStoryFailedError,
)
from app.core.deps import CurrentUser, PortfolioStoryServiceDep
from app.domain.exceptions import NotFoundError

router = APIRouter(prefix="/jobs", tags=["portfolio-story"])


@router.post(
    "/{job_id}/portfolio-story",
    response_model=PortfolioStoryRead,
    responses={204: {"description": "No portfolios to pick from"}},
)
async def generate_portfolio_story(
    job_id: UUID,
    user: CurrentUser,
    service: PortfolioStoryServiceDep,
) -> PortfolioStoryRead | Response:
    try:
        story = await service.build(user_id=user.id, job_id=job_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PortfolioStoryFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    if story is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return story
