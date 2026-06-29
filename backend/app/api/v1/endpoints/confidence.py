from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.application.dto.confidence_dto import JobConfidenceReport
from app.core.deps import CurrentUser, JobConfidenceServiceDep
from app.domain.exceptions import NotFoundError

router = APIRouter(prefix="/jobs", tags=["confidence"])


@router.get("/{job_id}/confidence", response_model=JobConfidenceReport)
async def get_confidence(
    job_id: UUID,
    user: CurrentUser,
    service: JobConfidenceServiceDep,
) -> JobConfidenceReport:
    try:
        return await service.build(user_id=user.id, job_id=job_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
