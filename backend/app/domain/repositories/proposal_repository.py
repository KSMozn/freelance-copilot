from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.proposal import Milestone, Proposal


class ProposalRepository(Protocol):
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
        prompt_version: str,
        model_provider: str,
        model_name: str,
        raw_response: dict[str, Any] | None,
    ) -> Proposal: ...

    async def get_by_id(self, proposal_id: UUID, *, user_id: UUID) -> Proposal | None: ...

    async def list_by_job_id(
        self, job_id: UUID, *, user_id: UUID
    ) -> list[Proposal]: ...

    async def get_latest_by_job_id(
        self, job_id: UUID, *, user_id: UUID
    ) -> Proposal | None: ...

    async def update(
        self,
        proposal_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> Proposal | None: ...

    async def delete(self, proposal_id: UUID, *, user_id: UUID) -> bool: ...
