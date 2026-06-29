from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dto.match_report_dto import (
    GapRecommendationRead,
    MatchReportRead,
)
from app.application.services.match_report_service import MatchReportService
from app.core.deps import CurrentUser, get_match_report_service
from app.domain.entities.match_report import MatchReport
from app.domain.exceptions import NotFoundError

router = APIRouter(prefix="/jobs", tags=["match-reports"])

MatchReportDep = Annotated[MatchReportService, Depends(get_match_report_service)]


def _to_read(report: MatchReport) -> MatchReportRead:
    return MatchReportRead(
        id=report.id,
        user_id=report.user_id,
        job_id=report.job_id,
        persona_id=report.persona_id,
        overall_match=report.overall_match,
        technical_fit=report.technical_fit,
        architecture_fit=report.architecture_fit,
        domain_fit=report.domain_fit,
        leadership_fit=report.leadership_fit,
        soft_skills_fit=report.soft_skills_fit,
        interview_chance=report.interview_chance,
        missing_critical_skills=report.missing_critical_skills,
        missing_recommendations=[
            GapRecommendationRead(**asdict(r))
            for r in report.missing_recommendations
        ],
        rationale=report.rationale,
        profile_version=report.profile_version,
        computed_at=report.computed_at,
    )


@router.post("/{job_id}/match-report", response_model=MatchReportRead)
async def build_match_report(
    job_id: UUID,
    user: CurrentUser,
    service: MatchReportDep,
    persona_id: UUID | None = None,
    force: bool = False,
) -> MatchReportRead:
    """Compute (or return cached) match report for ``(job_id, persona_id)``.

    Default persona is used when ``persona_id`` is omitted. Pass ``force=true``
    to re-run scoring even when a cached row exists.
    """
    try:
        report = await service.build_or_get(
            user_id=user.id,
            job_id=job_id,
            persona_id=persona_id,
            force=force,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return _to_read(report)


@router.get("/{job_id}/match-reports", response_model=list[MatchReportRead])
async def list_match_reports(
    job_id: UUID, user: CurrentUser, service: MatchReportDep
) -> list[MatchReportRead]:
    reports = await service.list_for_job(user_id=user.id, job_id=job_id)
    return [_to_read(r) for r in reports]
