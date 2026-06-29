from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.application import (
    Application,
    ApplicationHistoryEntry,
    ApplicationStatus,
)


class ApplicationRepository(Protocol):
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
    ) -> Application: ...

    async def get_by_id(
        self, application_id: UUID, *, user_id: UUID
    ) -> Application | None: ...

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        status: ApplicationStatus | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Application], int]: ...

    async def find_active_for_job(
        self, *, user_id: UUID, job_id: UUID
    ) -> Application | None:
        """Return the user's currently-active application for a job (any
        non-terminal status), or None.
        """

    async def update(
        self,
        application_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> Application | None: ...

    async def delete(self, application_id: UUID, *, user_id: UUID) -> bool: ...

    async def list_for_analytics(
        self,
        user_id: UUID,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[Application]:
        """Return every application for the user, optionally bounded by
        `created_at`. Order is insignificant — the analytics service
        aggregates in Python.
        """


class ApplicationHistoryRepository(Protocol):
    async def create(
        self,
        *,
        application_id: UUID,
        user_id: UUID | None,
        from_status: str | None,
        to_status: str,
        note: str | None,
    ) -> ApplicationHistoryEntry: ...

    async def list_for_application(
        self, application_id: UUID, *, user_id: UUID
    ) -> list[ApplicationHistoryEntry]: ...

    async def list_recent_for_user(
        self,
        user_id: UUID,
        *,
        limit: int,
    ) -> list[ApplicationHistoryEntry]:
        """Most-recent-first across all the user's applications."""
