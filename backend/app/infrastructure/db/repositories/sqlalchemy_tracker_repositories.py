from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.tracker import (
    FollowUpReminder as DomainReminder,
    InteractionChannel,
    InteractionDirection,
    InterviewEvent as DomainInterview,
    InterviewFormat,
    RecruiterInteraction as DomainInteraction,
)
from app.infrastructure.db.models.tracker import (
    FollowUpReminder,
    InterviewEvent,
    RecruiterInteraction,
)


def _interaction_to_domain(row: RecruiterInteraction) -> DomainInteraction:
    return DomainInteraction(
        id=row.id,
        application_id=row.application_id,
        user_id=row.user_id,
        channel=row.channel,  # type: ignore[arg-type]
        direction=row.direction,  # type: ignore[arg-type]
        occurred_at=row.occurred_at,
        contact_name=row.contact_name,
        summary=row.summary,
        raw_content=row.raw_content,
        created_at=row.created_at,
    )


def _interview_to_domain(row: InterviewEvent) -> DomainInterview:
    return DomainInterview(
        id=row.id,
        application_id=row.application_id,
        user_id=row.user_id,
        round_label=row.round_label,
        format=row.format,  # type: ignore[arg-type]
        scheduled_at=row.scheduled_at,
        duration_minutes=row.duration_minutes,
        interviewer_names=row.interviewer_names,
        interviewer_notes=row.interviewer_notes,
        my_feedback=row.my_feedback,
        outcome=row.outcome,  # type: ignore[arg-type]
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _reminder_to_domain(row: FollowUpReminder) -> DomainReminder:
    return DomainReminder(
        id=row.id,
        application_id=row.application_id,
        user_id=row.user_id,
        due_at=row.due_at,
        note=row.note,
        channel=row.channel,  # type: ignore[arg-type]
        completed_at=row.completed_at,
        created_at=row.created_at,
    )


# ---- Recruiter interactions ---------------------------------------------


class SQLAlchemyRecruiterInteractionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_application(
        self, *, user_id: UUID, application_id: UUID
    ) -> list[DomainInteraction]:
        stmt = (
            select(RecruiterInteraction)
            .where(RecruiterInteraction.user_id == user_id)
            .where(RecruiterInteraction.application_id == application_id)
            .order_by(RecruiterInteraction.occurred_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_interaction_to_domain(r) for r in rows]

    async def create(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        channel: InteractionChannel,
        direction: InteractionDirection,
        occurred_at: datetime,
        contact_name: str | None,
        summary: str | None,
        raw_content: str | None,
    ) -> DomainInteraction:
        row = RecruiterInteraction(
            user_id=user_id,
            application_id=application_id,
            channel=channel,
            direction=direction,
            occurred_at=occurred_at,
            contact_name=contact_name,
            summary=summary,
            raw_content=raw_content,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _interaction_to_domain(row)

    async def delete(
        self, *, user_id: UUID, interaction_id: UUID
    ) -> bool:
        row = await self._session.get(RecruiterInteraction, interaction_id)
        if row is None or row.user_id != user_id:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True


# ---- Interview events ----------------------------------------------------


class SQLAlchemyInterviewEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_application(
        self, *, user_id: UUID, application_id: UUID
    ) -> list[DomainInterview]:
        stmt = (
            select(InterviewEvent)
            .where(InterviewEvent.user_id == user_id)
            .where(InterviewEvent.application_id == application_id)
            .order_by(
                InterviewEvent.scheduled_at.asc().nullslast(),
                InterviewEvent.created_at.asc(),
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_interview_to_domain(r) for r in rows]

    async def create(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        round_label: str,
        format: InterviewFormat,
        scheduled_at: datetime | None,
        duration_minutes: int | None,
        interviewer_names: str | None,
    ) -> DomainInterview:
        row = InterviewEvent(
            user_id=user_id,
            application_id=application_id,
            round_label=round_label,
            format=format,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            interviewer_names=interviewer_names,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _interview_to_domain(row)

    async def update(
        self,
        *,
        user_id: UUID,
        event_id: UUID,
        patch: dict[str, Any],
    ) -> DomainInterview | None:
        row = await self._session.get(InterviewEvent, event_id)
        if row is None or row.user_id != user_id:
            return None
        for k, v in patch.items():
            if hasattr(row, k):
                setattr(row, k, v)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _interview_to_domain(row)

    async def delete(self, *, user_id: UUID, event_id: UUID) -> bool:
        row = await self._session.get(InterviewEvent, event_id)
        if row is None or row.user_id != user_id:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True


# ---- Follow-up reminders -------------------------------------------------


class SQLAlchemyFollowUpReminderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_application(
        self, *, user_id: UUID, application_id: UUID
    ) -> list[DomainReminder]:
        stmt = (
            select(FollowUpReminder)
            .where(FollowUpReminder.user_id == user_id)
            .where(FollowUpReminder.application_id == application_id)
            .order_by(FollowUpReminder.due_at.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_reminder_to_domain(r) for r in rows]

    async def list_open_for_user(
        self, *, user_id: UUID, limit: int = 50
    ) -> list[DomainReminder]:
        stmt = (
            select(FollowUpReminder)
            .where(FollowUpReminder.user_id == user_id)
            .where(FollowUpReminder.completed_at.is_(None))
            .order_by(FollowUpReminder.due_at.asc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_reminder_to_domain(r) for r in rows]

    async def create(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        due_at: datetime,
        note: str,
        channel: InteractionChannel | None,
    ) -> DomainReminder:
        row = FollowUpReminder(
            user_id=user_id,
            application_id=application_id,
            due_at=due_at,
            note=note,
            channel=channel,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _reminder_to_domain(row)

    async def mark_complete(
        self, *, user_id: UUID, reminder_id: UUID, completed_at: datetime
    ) -> DomainReminder | None:
        row = await self._session.get(FollowUpReminder, reminder_id)
        if row is None or row.user_id != user_id:
            return None
        row.completed_at = completed_at
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _reminder_to_domain(row)

    async def delete(
        self, *, user_id: UUID, reminder_id: UUID
    ) -> bool:
        row = await self._session.get(FollowUpReminder, reminder_id)
        if row is None or row.user_id != user_id:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True
