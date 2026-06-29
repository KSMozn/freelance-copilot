from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.application.dto.job_dto import CompanyResearchRequest, CompanyResearchSchema
from app.application.services.company_research_service import (
    CompanyResearchFailedError,
)
from app.core.deps import CompanyResearchServiceDep, CurrentUser
from app.domain.exceptions import NotFoundError

router = APIRouter(prefix="/jobs", tags=["research"])


@router.post("/{job_id}/research", response_model=CompanyResearchSchema)
async def run_company_research(
    job_id: UUID,
    payload: CompanyResearchRequest,
    user: CurrentUser,
    service: CompanyResearchServiceDep,
) -> CompanyResearchSchema:
    try:
        return await service.research(
            user_id=user.id,
            job_id=job_id,
            url=str(payload.url),
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CompanyResearchFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
