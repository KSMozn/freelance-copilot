from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.job import BudgetType, Job as DomainJob, JobStatus
from app.infrastructure.db.models.job import Job as JobModel


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
    ) -> tuple[list[DomainJob], int]:
        stmt = select(JobModel).where(JobModel.user_id == user_id)
        count_stmt = select(func.count(JobModel.id)).where(JobModel.user_id == user_id)
        if status is not None:
            stmt = stmt.where(JobModel.status == status)
            count_stmt = count_stmt.where(JobModel.status == status)
        if search:
            like = f"%{search}%"
            cond = or_(JobModel.title.ilike(like), JobModel.description.ilike(like))
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        stmt = stmt.order_by(JobModel.created_at.desc()).limit(limit).offset(offset)
        rows = (await self._session.execute(stmt)).scalars().all()
        total = (await self._session.execute(count_stmt)).scalar_one()
        return [_to_domain(r) for r in rows], total

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
