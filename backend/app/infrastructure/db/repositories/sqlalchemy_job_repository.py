from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Integer, func, nulls_last, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.analysis import OpportunityScore as DomainOpportunityScore
from app.domain.entities.job import (
    BudgetType,
    CompanyResearch,
    JobStatus,
)
from app.domain.entities.job import (
    Job as DomainJob,
)
from app.infrastructure.db.models.job import Job as JobModel


def _research_from_jsonb(raw: dict | None) -> CompanyResearch | None:
    if not isinstance(raw, dict) or not raw.get("source_url"):
        return None
    fetched_raw = raw.get("fetched_at")
    fetched: datetime | None = None
    if isinstance(fetched_raw, str):
        try:
            fetched = datetime.fromisoformat(fetched_raw.replace("Z", "+00:00"))
        except ValueError:
            fetched = None
    return CompanyResearch(
        source_url=str(raw["source_url"]),
        business_domain=raw.get("business_domain"),
        product_summary=raw.get("product_summary"),
        target_customers=raw.get("target_customers"),
        existing_stack=[str(s) for s in (raw.get("existing_stack") or []) if s],
        funding_signals=raw.get("funding_signals"),
        likely_architecture=raw.get("likely_architecture"),
        personalization_hook=raw.get("personalization_hook"),
        fetched_at=fetched,
    )


def _research_to_jsonb(r: CompanyResearch | None) -> dict | None:
    if r is None:
        return None
    return {
        "source_url": r.source_url,
        "business_domain": r.business_domain,
        "product_summary": r.product_summary,
        "target_customers": r.target_customers,
        "existing_stack": list(r.existing_stack),
        "funding_signals": r.funding_signals,
        "likely_architecture": r.likely_architecture,
        "personalization_hook": r.personalization_hook,
        "fetched_at": r.fetched_at.isoformat() if r.fetched_at else None,
    }
from app.infrastructure.db.models.opportunity_score import (
    OpportunityScore as OpportunityScoreModel,
)

_BREAKDOWN_SORT_KEYS = {
    "technical_fit",
    "domain_fit",
    "proposal_count",
    "budget_attractiveness",
    "client_quality",
    "estimated_effort",
    "risk_level",
    "strategic_value",
}


def _score_to_domain(row: OpportunityScoreModel) -> DomainOpportunityScore:
    return DomainOpportunityScore(
        id=row.id,
        job_id=row.job_id,
        analysis_id=row.analysis_id,
        score=row.score,
        recommendation=row.recommendation,
        confidence=row.confidence,
        score_breakdown=dict(row.score_breakdown),
        reasoning=row.reasoning,
        profile_version=row.profile_version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_domain(row: JobModel) -> DomainJob:
    return DomainJob(
        id=row.id,
        user_id=row.user_id,
        title=row.title,
        description=row.description,
        source_url=row.source_url,
        budget_type=row.budget_type,
        budget_min=row.budget_min,
        budget_max=row.budget_max,
        currency=row.currency,
        proposal_count=row.proposal_count,
        client_id=row.client_id,
        status=row.status,
        source_hash=row.source_hash,
        version=row.version,
        imported_at=row.imported_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
        client_research=_research_from_jsonb(row.client_research),
    )


class SQLAlchemyJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        title: str,
        description: str,
        source_hash: str,
        source_url: str | None,
        budget_type: BudgetType | None,
        budget_min: Decimal | None,
        budget_max: Decimal | None,
        currency: str,
        proposal_count: int | None,
        status: JobStatus,
    ) -> DomainJob:
        # versioning: if an older row exists with same hash, bump version
        prev_stmt = (
            select(func.max(JobModel.version))
            .where(JobModel.user_id == user_id, JobModel.source_hash == source_hash)
        )
        prev_version = (await self._session.execute(prev_stmt)).scalar()
        version = (prev_version or 0) + 1

        row = JobModel(
            user_id=user_id,
            title=title,
            description=description,
            source_url=source_url,
            budget_type=budget_type,
            budget_min=budget_min,
            budget_max=budget_max,
            currency=currency,
            proposal_count=proposal_count,
            status=status,
            source_hash=source_hash,
            version=version,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def get_by_id(self, job_id: UUID, *, user_id: UUID) -> DomainJob | None:
        stmt = select(JobModel).where(JobModel.id == job_id, JobModel.user_id == user_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def get_by_source_hash(self, source_hash: str, *, user_id: UUID) -> DomainJob | None:
        stmt = (
            select(JobModel)
            .where(JobModel.user_id == user_id, JobModel.source_hash == source_hash)
            .order_by(JobModel.version.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        status: JobStatus | None,
        limit: int,
        offset: int,
        search: str | None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> tuple[list[tuple[DomainJob, DomainOpportunityScore | None]], int]:
        stmt = select(JobModel, OpportunityScoreModel).join(
            OpportunityScoreModel,
            OpportunityScoreModel.job_id == JobModel.id,
            isouter=True,
        ).where(JobModel.user_id == user_id)
        count_stmt = select(func.count(JobModel.id)).where(JobModel.user_id == user_id)
        if status is not None:
            stmt = stmt.where(JobModel.status == status)
            count_stmt = count_stmt.where(JobModel.status == status)
        if search:
            like = f"%{search}%"
            cond = or_(JobModel.title.ilike(like), JobModel.description.ilike(like))
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        sort_col = self._resolve_sort_column(sort_by)
        direction = sort_dir.lower()
        ordered = sort_col.desc() if direction != "asc" else sort_col.asc()
        # Always sort jobs without a score last, then break ties on created_at desc.
        if sort_by != "created_at" and sort_by != "title":
            ordered = nulls_last(ordered)
        stmt = stmt.order_by(ordered, JobModel.created_at.desc()).limit(limit).offset(offset)

        rows = (await self._session.execute(stmt)).all()
        total = (await self._session.execute(count_stmt)).scalar_one()
        items: list[tuple[DomainJob, DomainOpportunityScore | None]] = []
        for job_row, score_row in rows:
            items.append(
                (
                    _to_domain(job_row),
                    _score_to_domain(score_row) if score_row is not None else None,
                )
            )
        return items, total

    @staticmethod
    def _resolve_sort_column(sort_by: str):
        if sort_by == "title":
            return JobModel.title
        if sort_by == "score":
            return OpportunityScoreModel.score
        if sort_by.startswith("score."):
            key = sort_by.split(".", 1)[1]
            if key not in _BREAKDOWN_SORT_KEYS:
                return JobModel.created_at
            return OpportunityScoreModel.score_breakdown[key].astext.cast(Integer)
        return JobModel.created_at

    async def update(
        self,
        job_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> DomainJob | None:
        stmt = select(JobModel).where(JobModel.id == job_id, JobModel.user_id == user_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if not row:
            return None
        for k, v in fields.items():
            setattr(row, k, v)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def delete(self, job_id: UUID, *, user_id: UUID) -> bool:
        stmt = select(JobModel).where(JobModel.id == job_id, JobModel.user_id == user_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if not row:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True
