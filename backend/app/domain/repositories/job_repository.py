from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.domain.entities.job import BudgetType, Job, JobStatus


class JobRepository(Protocol):
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
    ) -> Job: ...

    async def get_by_id(self, job_id: UUID, *, user_id: UUID) -> Job | None: ...

    async def get_by_source_hash(self, source_hash: str, *, user_id: UUID) -> Job | None: ...

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        status: JobStatus | None,
        limit: int,
        offset: int,
        search: str | None,
    ) -> tuple[list[Job], int]: ...

    async def update(
        self,
        job_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> Job | None: ...

    async def delete(self, job_id: UUID, *, user_id: UUID) -> bool: ...
