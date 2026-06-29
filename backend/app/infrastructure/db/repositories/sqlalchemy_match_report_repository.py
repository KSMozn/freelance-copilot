from dataclasses import asdict
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.match_report import GapRecommendation
from app.domain.entities.match_report import MatchReport as DomainReport
from app.infrastructure.db.models.match_report import MatchReport


def _to_domain(row: MatchReport) -> DomainReport:
    recs = [
        GapRecommendation(
            skill=str(r.get("skill", "")),
            kind=r.get("kind", "learning_resource"),
            suggestion=str(r.get("suggestion", "")),
            effort_estimate=str(r.get("effort_estimate", "")),
            priority=int(r.get("priority", 3)),
        )
        for r in (row.missing_recommendations or [])
        if isinstance(r, dict)
    ]
    return DomainReport(
        id=row.id,
        user_id=row.user_id,
        job_id=row.job_id,
        persona_id=row.persona_id,
        overall_match=row.overall_match,
        technical_fit=row.technical_fit,
        architecture_fit=row.architecture_fit,
        domain_fit=row.domain_fit,
        leadership_fit=row.leadership_fit,
        soft_skills_fit=row.soft_skills_fit,
        interview_chance=row.interview_chance,  # type: ignore[arg-type]
        missing_critical_skills=list(row.missing_critical_skills or []),
        missing_recommendations=recs,
        rationale=list(row.rationale or []),
        profile_version=row.profile_version,
        computed_at=row.computed_at,
    )


def _recs_to_jsonb(recs: list[GapRecommendation]) -> list[dict[str, Any]]:
    return [asdict(r) for r in recs]


class SQLAlchemyMatchReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_job(
        self, *, user_id: UUID, job_id: UUID
    ) -> list[DomainReport]:
        stmt = (
            select(MatchReport)
            .where(MatchReport.user_id == user_id, MatchReport.job_id == job_id)
            .order_by(MatchReport.overall_match.desc(), MatchReport.computed_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(r) for r in rows]

    async def get_for_pair(
        self, *, user_id: UUID, job_id: UUID, persona_id: UUID | None
    ) -> DomainReport | None:
        stmt = select(MatchReport).where(
            MatchReport.user_id == user_id, MatchReport.job_id == job_id
        )
        if persona_id is None:
            stmt = stmt.where(MatchReport.persona_id.is_(None))
        else:
            stmt = stmt.where(MatchReport.persona_id == persona_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def upsert(
        self, report: DomainReport, *, payload: dict[str, Any]
    ) -> DomainReport:
        # Find by (job, persona) — the UNIQUE constraint guarantees one row.
        stmt = select(MatchReport).where(
            MatchReport.job_id == report.job_id
        )
        if report.persona_id is None:
            stmt = stmt.where(MatchReport.persona_id.is_(None))
        else:
            stmt = stmt.where(MatchReport.persona_id == report.persona_id)
        existing = (await self._session.execute(stmt)).scalar_one_or_none()

        recs_json = _recs_to_jsonb(report.missing_recommendations)
        values: dict[str, Any] = {
            "user_id": report.user_id,
            "job_id": report.job_id,
            "persona_id": report.persona_id,
            "overall_match": report.overall_match,
            "technical_fit": report.technical_fit,
            "architecture_fit": report.architecture_fit,
            "domain_fit": report.domain_fit,
            "leadership_fit": report.leadership_fit,
            "soft_skills_fit": report.soft_skills_fit,
            "interview_chance": report.interview_chance,
            "missing_critical_skills": list(report.missing_critical_skills or []),
            "missing_recommendations": recs_json,
            "rationale": list(report.rationale or []),
            "profile_version": report.profile_version,
        }
        # Caller may inject overrides (e.g. computed_at).
        values.update(payload)

        if existing is None:
            row = MatchReport(**values)
            self._session.add(row)
        else:
            for k, v in values.items():
                setattr(existing, k, v)
            row = existing
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)
