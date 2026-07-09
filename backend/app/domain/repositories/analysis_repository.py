from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.analysis import (
    JobAnalysis,
    OpportunityScore,
    RiskItem,
    StackRequirement,
)


class JobAnalysisRepository(Protocol):
    async def get_by_job_id(self, job_id: UUID) -> JobAnalysis | None: ...

    async def list_for_user(self, user_id: UUID) -> list[JobAnalysis]:
        """All analyses owned (transitively, via jobs.user_id) by ``user_id``.

        Phase G aggregates across this list to compute market-demand signals.
        """
        ...

    async def upsert(
        self,
        *,
        job_id: UUID,
        summary: str | None,
        required_skills: list[str],
        preferred_skills: list[str],
        technologies: list[str],
        business_domain: str | None,
        seniority: str | None,
        complexity: str | None,
        estimated_hours_min: int | None,
        estimated_hours_max: int | None,
        budget_assessment: str | None,
        client_intent: str | None,
        hidden_requirements: list[str],
        expected_deliverables: list[str],
        risks: list[RiskItem],
        red_flags: list[str],
        green_flags: list[str],
        questions_to_ask_client: list[str],
        risk_level: str | None,
        communication_required: str | None,
        provider: str,
        model: str,
        prompt_version: str,
        stack_requirements: list[StackRequirement],
        raw_response: dict[str, Any] | None,
    ) -> JobAnalysis: ...


class OpportunityScoreRepository(Protocol):
    async def get_by_job_id(self, job_id: UUID) -> OpportunityScore | None: ...

    async def upsert(
        self,
        *,
        job_id: UUID,
        analysis_id: UUID,
        score: int,
        recommendation: str,
        confidence: str,
        score_breakdown: dict[str, int],
        reasoning: str,
        profile_version: str,
    ) -> OpportunityScore: ...
