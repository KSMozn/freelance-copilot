from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.application.dto.resume_dto import ResumeRecommendationsResponse
from app.core.deps import CurrentUser, ResumeRecommendationServiceDep
from app.domain.exceptions import NotFoundError

router = APIRouter(prefix="/jobs", tags=["resume-recommendation"])


@router.post(
    "/{job_id}/recommend-resume",
    response_model=ResumeRecommendationsResponse,
    status_code=status.HTTP_200_OK,
)
async def recommend_resume(
    job_id: UUID,
    user: CurrentUser,
    service: ResumeRecommendationServiceDep,
    top_n: int = Query(default=3, ge=1, le=10),
) -> ResumeRecommendationsResponse:
    """Rank the user's resume profiles for an analyzed job."""
    try:
        return await service.recommend(user_id=user.id, job_id=job_id, top_n=top_n)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{job_id}/resume-recommendations",
    response_model=ResumeRecommendationsResponse,
)
async def get_resume_recommendations(
    job_id: UUID,
    user: CurrentUser,
    service: ResumeRecommendationServiceDep,
    top_n: int = Query(default=3, ge=1, le=10),
) -> ResumeRecommendationsResponse:
    return await recommend_resume(
        job_id=job_id, user=user, service=service, top_n=top_n
    )
