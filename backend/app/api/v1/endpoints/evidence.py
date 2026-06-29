from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.application.dto.evidence_dto import EvidenceReport
from app.core.deps import CurrentUser, SkillEvidenceServiceDep
from app.domain.exceptions import NotFoundError

router = APIRouter(prefix="/jobs", tags=["evidence"])


@router.get("/{job_id}/evidence", response_model=EvidenceReport)
async def get_evidence(
    job_id: UUID,
    user: CurrentUser,
    service: SkillEvidenceServiceDep,
) -> EvidenceReport:
    try:
        return await service.build(user_id=user.id, job_id=job_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
