from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.application.dto.analysis_dto import JobAnalysisResponse
from app.application.services.job_analysis_service import AnalysisFailedError
from app.core.deps import CurrentUser, JobAnalysisServiceDep
from app.domain.exceptions import NotFoundError

router = APIRouter(prefix="/jobs", tags=["analysis"])


@router.post(
    "/{job_id}/analyze",
    response_model=JobAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_job(
    job_id: UUID,
    user: CurrentUser,
    service: JobAnalysisServiceDep,
) -> JobAnalysisResponse:
    """Run AI analysis + scoring for a job. Upserts on re-run."""
    try:
        return await service.analyze(user_id=user.id, job_id=job_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AnalysisFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc


@router.post(
    "/{job_id}/reanalyze",
    response_model=JobAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def reanalyze_job(
    job_id: UUID,
    user: CurrentUser,
    service: JobAnalysisServiceDep,
) -> JobAnalysisResponse:
    """Alias of /analyze. Provided for clarity in clients that want explicit re-runs."""
    return await analyze_job(job_id=job_id, user=user, service=service)


@router.get("/{job_id}/analysis", response_model=JobAnalysisResponse)
async def get_analysis(
    job_id: UUID,
    user: CurrentUser,
    service: JobAnalysisServiceDep,
) -> JobAnalysisResponse:
    try:
        return await service.get(user_id=user.id, job_id=job_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
