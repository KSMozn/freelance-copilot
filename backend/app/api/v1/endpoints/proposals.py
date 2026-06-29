"""Phase 5 endpoints.

Two routers in one file:

- `job_proposals_router` — endpoints scoped under /jobs/{job_id}/proposals
- `proposals_router`     — endpoints scoped under /proposals/{proposal_id}
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.application.dto.proposal_dto import (
    ProposalGenerateRequest,
    ProposalRead,
    ProposalReviewResult,
    ProposalUpdateRequest,
    QualityBreakdown,
)
from app.application.services.proposal_generation_service import (
    ProposalGenerationFailedError,
)
from app.core.deps import CurrentUser, ProposalGenerationServiceDep
from app.domain.exceptions import NotFoundError

job_proposals_router = APIRouter(prefix="/jobs", tags=["proposals"])
proposals_router = APIRouter(prefix="/proposals", tags=["proposals"])


@job_proposals_router.post(
    "/{job_id}/proposals/generate",
    response_model=ProposalRead,
    status_code=status.HTTP_200_OK,
)
async def generate_proposal(
    job_id: UUID,
    user: CurrentUser,
    service: ProposalGenerationServiceDep,
    payload: ProposalGenerateRequest | None = None,
) -> ProposalRead:
    """Run analyzer → matches → recommend → generate → review for a job."""
    body = payload or ProposalGenerateRequest()
    try:
        return await service.generate(
            user_id=user.id,
            job_id=job_id,
            top_portfolio_n=body.top_portfolio_n,
            top_resume_n=body.top_resume_n,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProposalGenerationFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc


@job_proposals_router.get(
    "/{job_id}/proposals/latest",
    response_model=ProposalRead,
)
async def get_latest_proposal(
    job_id: UUID,
    user: CurrentUser,
    service: ProposalGenerationServiceDep,
) -> ProposalRead:
    result = await service.get_latest_for_job(user_id=user.id, job_id=job_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No proposal generated for this job yet.",
        )
    return result


@job_proposals_router.get(
    "/{job_id}/proposals",
    response_model=list[ProposalRead],
)
async def list_proposals_for_job(
    job_id: UUID,
    user: CurrentUser,
    service: ProposalGenerationServiceDep,
) -> list[ProposalRead]:
    return await service.list_for_job(user_id=user.id, job_id=job_id)


@proposals_router.get(
    "/{proposal_id}",
    response_model=ProposalRead,
)
async def get_proposal(
    proposal_id: UUID,
    user: CurrentUser,
    service: ProposalGenerationServiceDep,
) -> ProposalRead:
    try:
        return await service.get(user_id=user.id, proposal_id=proposal_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@proposals_router.put(
    "/{proposal_id}",
    response_model=ProposalRead,
)
async def update_proposal(
    proposal_id: UUID,
    payload: ProposalUpdateRequest,
    user: CurrentUser,
    service: ProposalGenerationServiceDep,
) -> ProposalRead:
    fields = payload.model_dump(exclude_unset=True)
    if "milestones" in fields and fields["milestones"] is not None:
        # Pydantic gave us MilestoneRead instances — service expects dicts.
        fields["milestones"] = [m if isinstance(m, dict) else m.model_dump() for m in fields["milestones"]]
    try:
        return await service.update(
            user_id=user.id, proposal_id=proposal_id, fields=fields
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@proposals_router.delete(
    "/{proposal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_proposal(
    proposal_id: UUID,
    user: CurrentUser,
    service: ProposalGenerationServiceDep,
) -> None:
    try:
        await service.delete(user_id=user.id, proposal_id=proposal_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@proposals_router.post(
    "/{proposal_id}/review",
    response_model=ProposalReviewResult,
)
async def review_proposal(
    proposal_id: UUID,
    user: CurrentUser,
    service: ProposalGenerationServiceDep,
) -> ProposalReviewResult:
    """Re-run the deterministic review against the current proposal body."""
    try:
        updated = await service.re_review(
            user_id=user.id, proposal_id=proposal_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProposalReviewResult(
        quality_score=updated.quality_score or 0,
        quality_breakdown=QualityBreakdown(**(updated.quality_breakdown or {})),
        warnings=updated.quality_warnings,
    )
