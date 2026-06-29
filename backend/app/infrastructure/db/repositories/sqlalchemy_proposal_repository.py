from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.proposal import (
    ImplementationWeek,
    Milestone,
    Proposal as DomainProposal,
    ProposalDiagram,
    ProposalStrategy,
)
from app.infrastructure.db.models.proposal import Proposal as ProposalModel


def _diagrams_from_jsonb(raw: list[Any] | None) -> list[ProposalDiagram]:
    if not raw:
        return []
    out: list[ProposalDiagram] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        mermaid = str(item.get("mermaid", "")).strip()
        if not mermaid:
            continue
        out.append(
            ProposalDiagram(
                kind=str(item.get("kind", "system")),
                title=str(item.get("title", "")),
                mermaid=mermaid,
            )
        )
    return out


def _diagrams_to_jsonb(diagrams: list[ProposalDiagram]) -> list[dict[str, Any]]:
    return [
        {"kind": d.kind, "title": d.title, "mermaid": d.mermaid}
        for d in diagrams
    ]


def _plan_from_jsonb(raw: list[Any] | None) -> list[ImplementationWeek]:
    if not raw:
        return []
    out: list[ImplementationWeek] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            week = int(item.get("week", 0))
        except (TypeError, ValueError):
            continue
        if week <= 0:
            continue
        out.append(
            ImplementationWeek(
                week=week,
                focus=str(item.get("focus", "")),
                summary=str(item.get("summary", "")),
                deliverables=[str(d) for d in (item.get("deliverables") or []) if d],
            )
        )
    out.sort(key=lambda w: w.week)
    return out


def _plan_to_jsonb(weeks: list[ImplementationWeek]) -> list[dict[str, Any]]:
    return [
        {
            "week": w.week,
            "focus": w.focus,
            "summary": w.summary,
            "deliverables": list(w.deliverables),
        }
        for w in weeks
    ]


def _strategy_from_jsonb(raw: dict[str, Any] | None) -> ProposalStrategy | None:
    if not isinstance(raw, dict):
        return None
    angle = raw.get("angle")
    if not angle:
        return None
    points = raw.get("emphasis_points") or []
    return ProposalStrategy(
        angle=str(angle),
        rationale=str(raw.get("rationale", "")),
        emphasis_points=[str(p) for p in points if p],
    )


def _strategy_to_jsonb(strategy: ProposalStrategy | None) -> dict[str, Any] | None:
    if strategy is None:
        return None
    return {
        "angle": strategy.angle,
        "rationale": strategy.rationale,
        "emphasis_points": list(strategy.emphasis_points),
    }


def _milestones_to_jsonb(milestones: list[Milestone]) -> list[dict[str, Any]]:
    return [
        {
            "name": m.name,
            "description": m.description,
            "estimated_hours": m.estimated_hours,
        }
        for m in milestones
    ]


def _milestones_from_jsonb(raw: list[Any] | None) -> list[Milestone]:
    if not raw:
        return []
    out: list[Milestone] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        out.append(
            Milestone(
                name=str(item.get("name", "")),
                description=str(item.get("description", "")),
                estimated_hours=item.get("estimated_hours"),
            )
        )
    return out


def _to_domain(row: ProposalModel) -> DomainProposal:
    portfolio_ids = []
    for pid in row.portfolio_ids or []:
        try:
            portfolio_ids.append(UUID(str(pid)))
        except (ValueError, TypeError):
            continue
    return DomainProposal(
        id=row.id,
        user_id=row.user_id,
        job_id=row.job_id,
        resume_id=row.resume_id,
        portfolio_ids=portfolio_ids,
        title=row.title,
        body=row.body,
        short_body=row.short_body,
        questions=list(row.questions or []),
        milestones=_milestones_from_jsonb(row.milestones),
        delivery_approach=list(row.delivery_approach or []),
        risk_notes=list(row.risk_notes or []),
        quality_score=row.quality_score,
        quality_breakdown=row.quality_breakdown,
        quality_warnings=list(row.quality_warnings or []),
        strategy=_strategy_from_jsonb(row.strategy),
        implementation_plan=_plan_from_jsonb(row.implementation_plan),
        diagrams=_diagrams_from_jsonb(row.diagrams),
        prompt_version=row.prompt_version,
        model_provider=row.model_provider,
        model_name=row.model_name,
        raw_response=row.raw_response,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyProposalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
        resume_id: UUID | None,
        portfolio_ids: list[UUID],
        title: str | None,
        body: str,
        short_body: str | None,
        questions: list[str],
        milestones: list[Milestone],
        delivery_approach: list[str],
        risk_notes: list[str],
        quality_score: int | None,
        quality_breakdown: dict[str, int] | None,
        quality_warnings: list[str],
        strategy: ProposalStrategy | None,
        implementation_plan: list[ImplementationWeek],
        diagrams: list[ProposalDiagram],
        prompt_version: str,
        model_provider: str,
        model_name: str,
        raw_response: dict[str, Any] | None,
    ) -> DomainProposal:
        row = ProposalModel(
            user_id=user_id,
            job_id=job_id,
            resume_id=resume_id,
            portfolio_ids=[str(pid) for pid in portfolio_ids],
            title=title,
            body=body,
            short_body=short_body,
            questions=questions,
            milestones=_milestones_to_jsonb(milestones),
            delivery_approach=delivery_approach,
            risk_notes=risk_notes,
            quality_score=quality_score,
            quality_breakdown=quality_breakdown,
            quality_warnings=quality_warnings,
            strategy=_strategy_to_jsonb(strategy),
            implementation_plan=_plan_to_jsonb(implementation_plan),
            diagrams=_diagrams_to_jsonb(diagrams),
            prompt_version=prompt_version,
            model_provider=model_provider,
            model_name=model_name,
            raw_response=raw_response,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def get_by_id(
        self, proposal_id: UUID, *, user_id: UUID
    ) -> DomainProposal | None:
        stmt = select(ProposalModel).where(
            ProposalModel.id == proposal_id, ProposalModel.user_id == user_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def list_by_job_id(
        self, job_id: UUID, *, user_id: UUID
    ) -> list[DomainProposal]:
        stmt = (
            select(ProposalModel)
            .where(ProposalModel.job_id == job_id, ProposalModel.user_id == user_id)
            .order_by(ProposalModel.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(r) for r in rows]

    async def get_latest_by_job_id(
        self, job_id: UUID, *, user_id: UUID
    ) -> DomainProposal | None:
        stmt = (
            select(ProposalModel)
            .where(ProposalModel.job_id == job_id, ProposalModel.user_id == user_id)
            .order_by(ProposalModel.created_at.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def update(
        self,
        proposal_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> DomainProposal | None:
        stmt = select(ProposalModel).where(
            ProposalModel.id == proposal_id, ProposalModel.user_id == user_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if not row:
            return None
        for k, v in fields.items():
            if k == "milestones" and isinstance(v, list):
                row.milestones = _milestones_to_jsonb(
                    [
                        m if isinstance(m, Milestone) else Milestone(**m)
                        for m in v
                    ]
                )
            elif k == "portfolio_ids" and isinstance(v, list):
                row.portfolio_ids = [str(pid) for pid in v]
            else:
                setattr(row, k, v)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def delete(self, proposal_id: UUID, *, user_id: UUID) -> bool:
        stmt = select(ProposalModel).where(
            ProposalModel.id == proposal_id, ProposalModel.user_id == user_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if not row:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True
