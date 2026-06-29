from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.tracker import (
    FollowUpReminder,
    InteractionChannel,
    InteractionDirection,
    InterviewEvent,
    InterviewFormat,
    RecruiterInteraction,
)


class RecruiterInteractionRepository(Protocol):
    async def list_for_application(
        self, *, user_id: UUID, application_id: UUID
    ) -> list[RecruiterInteraction]: ...

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
    ) -> RecruiterInteraction: ...

    async def delete(
        self, *, user_id: UUID, interaction_id: UUID
    ) -> bool: ...


class InterviewEventRepository(Protocol):
    async def list_for_application(
        self, *, user_id: UUID, application_id: UUID
    ) -> list[InterviewEvent]: ...

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
    ) -> InterviewEvent: ...

    async def update(
        self,
        *,
        user_id: UUID,
        event_id: UUID,
        patch: dict[str, Any],
    ) -> InterviewEvent | None: ...

    async def delete(self, *, user_id: UUID, event_id: UUID) -> bool: ...


class FollowUpReminderRepository(Protocol):
    async def list_for_application(
        self, *, user_id: UUID, application_id: UUID
    ) -> list[FollowUpReminder]: ...

    async def list_open_for_user(
        self, *, user_id: UUID, limit: int = 50
    ) -> list[FollowUpReminder]: ...

    async def create(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        due_at: datetime,
        note: str,
        channel: InteractionChannel | None,
    ) -> FollowUpReminder: ...

    async def mark_complete(
        self, *, user_id: UUID, reminder_id: UUID, completed_at: datetime
    ) -> FollowUpReminder | None: ...

    async def delete(
        self, *, user_id: UUID, reminder_id: UUID
    ) -> bool: ...
