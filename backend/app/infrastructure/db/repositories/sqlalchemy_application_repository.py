from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.application import (
    TERMINAL_STATUSES,
    ApplicationHistoryEntry,
    ApplicationStatus,
)
from app.domain.entities.application import (
    Application as DomainApplication,
)
from app.infrastructure.db.models.application import (
    Application as ApplicationModel,
)
from app.infrastructure.db.models.application import (
    ApplicationHistory as ApplicationHistoryModel,
)
from app.infrastructure.db.models.job import Job as JobModel


def _to_domain(row: ApplicationModel) -> DomainApplication:
    portfolio_ids: list[UUID] = []
    for pid in row.portfolio_ids or []:
        try:
            portfolio_ids.append(UUID(str(pid)))
        except (ValueError, TypeError):
            continue
    return DomainApplication(
        id=row.id,
        user_id=row.user_id,
        job_id=row.job_id,
        proposal_id=row.proposal_id,
        resume_id=row.resume_id,
        portfolio_ids=portfolio_ids,
        status=ApplicationStatus(row.status),
        applied_at=row.applied_at,
        viewed_at=row.viewed_at,
        interview_at=row.interview_at,
        offer_at=row.offer_at,
        won_at=row.won_at,
        rejected_at=row.rejected_at,
        withdrawn_at=row.withdrawn_at,
        completed_at=row.completed_at,
        contract_amount=row.contract_amount,
        client_response=row.client_response,
        rejection_reason=row.rejection_reason,
        notes=row.notes,
        snapshot=row.snapshot,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _history_to_domain(row: ApplicationHistoryModel) -> ApplicationHistoryEntry:
    return ApplicationHistoryEntry(
        id=row.id,
        application_id=row.application_id,
        user_id=row.user_id,
        from_status=row.from_status,
        to_status=row.to_status,
        note=row.note,
        created_at=row.created_at,
    )


class SQLAlchemyApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
        proposal_id: UUID | None,
        resume_id: UUID | None,
        portfolio_ids: list[UUID],
        status: ApplicationStatus,
        applied_at: object | None,
        snapshot: dict[str, Any] | None,
    ) -> DomainApplication:
        row = ApplicationModel(
            user_id=user_id,
            job_id=job_id,
            proposal_id=proposal_id,
            resume_id=resume_id,
            portfolio_ids=[str(pid) for pid in portfolio_ids],
            status=status.value,
            applied_at=applied_at,
            snapshot=snapshot,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def get_by_id(
        self, application_id: UUID, *, user_id: UUID
    ) -> DomainApplication | None:
        stmt = select(ApplicationModel).where(
            ApplicationModel.id == application_id, ApplicationModel.user_id == user_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        status: ApplicationStatus | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[DomainApplication], int]:
        stmt = select(ApplicationModel).where(ApplicationModel.user_id == user_id)
        count_stmt = select(func.count(ApplicationModel.id)).where(
            ApplicationModel.user_id == user_id
        )
        if status is not None:
            stmt = stmt.where(ApplicationModel.status == status.value)
            count_stmt = count_stmt.where(ApplicationModel.status == status.value)
        if search:
            # Search by job title via a join.
            like = f"%{search}%"
            stmt = stmt.join(JobModel, JobModel.id == ApplicationModel.job_id).where(
                JobModel.title.ilike(like)
            )
            count_stmt = (
                count_stmt.join(JobModel, JobModel.id == ApplicationModel.job_id)
                .where(JobModel.title.ilike(like))
            )
        stmt = stmt.order_by(ApplicationModel.created_at.desc()).limit(limit).offset(offset)
        rows = (await self._session.execute(stmt)).scalars().all()
        total = (await self._session.execute(count_stmt)).scalar_one()
        return [_to_domain(r) for r in rows], total

    async def find_active_for_job(
        self, *, user_id: UUID, job_id: UUID
    ) -> DomainApplication | None:
        terminal = [s.value for s in TERMINAL_STATUSES]
        stmt = (
            select(ApplicationModel)
            .where(
                ApplicationModel.user_id == user_id,
                ApplicationModel.job_id == job_id,
                ~ApplicationModel.status.in_(terminal),
            )
            .order_by(ApplicationModel.created_at.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def update(
        self,
        application_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> DomainApplication | None:
        stmt = select(ApplicationModel).where(
            ApplicationModel.id == application_id,
            ApplicationModel.user_id == user_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if not row:
            return None
        for k, v in fields.items():
            if k == "portfolio_ids" and isinstance(v, list):
                row.portfolio_ids = [str(pid) for pid in v]
            elif k == "status" and isinstance(v, ApplicationStatus):
                row.status = v.value
            else:
                setattr(row, k, v)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def delete(self, application_id: UUID, *, user_id: UUID) -> bool:
        stmt = select(ApplicationModel).where(
            ApplicationModel.id == application_id,
            ApplicationModel.user_id == user_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if not row:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True

    async def list_for_analytics(
        self,
        user_id: UUID,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[DomainApplication]:
        stmt = select(ApplicationModel).where(ApplicationModel.user_id == user_id)
        if from_date is not None:
            stmt = stmt.where(ApplicationModel.created_at >= from_date)
        if to_date is not None:
            stmt = stmt.where(ApplicationModel.created_at <= to_date)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(r) for r in rows]


class SQLAlchemyApplicationHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        application_id: UUID,
        user_id: UUID | None,
        from_status: str | None,
        to_status: str,
        note: str | None,
    ) -> ApplicationHistoryEntry:
        row = ApplicationHistoryModel(
            application_id=application_id,
            user_id=user_id,
            from_status=from_status,
            to_status=to_status,
            note=note,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _history_to_domain(row)

    async def list_for_application(
        self, application_id: UUID, *, user_id: UUID
    ) -> list[ApplicationHistoryEntry]:
        stmt = (
            select(ApplicationHistoryModel)
            .where(
                ApplicationHistoryModel.application_id == application_id,
                or_(
                    ApplicationHistoryModel.user_id == user_id,
                    ApplicationHistoryModel.user_id.is_(None),
                ),
            )
            .order_by(ApplicationHistoryModel.created_at.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_history_to_domain(r) for r in rows]

    async def list_recent_for_user(
        self,
        user_id: UUID,
        *,
        limit: int,
    ) -> list[ApplicationHistoryEntry]:
        stmt = (
            select(ApplicationHistoryModel)
            .where(ApplicationHistoryModel.user_id == user_id)
            .order_by(ApplicationHistoryModel.created_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_history_to_domain(r) for r in rows]
