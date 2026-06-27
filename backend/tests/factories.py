"""Tiny in-memory fakes used by Phase-2 unit tests.

These let us exercise the application layer end-to-end without a Postgres
instance: just a mock AI provider, fake repos, and a real ScoringService.
"""
from __future__ import annotations

from dataclasses import field, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from app.domain.entities.analysis import (
    JobAnalysis as DomainAnalysis,
    OpportunityScore as DomainScore,
    RiskItem,
)
from app.domain.entities.job import BudgetType, Job, JobStatus


def make_job(
    *,
    user_id: UUID | None = None,
    title: str = "Build a FastAPI backend",
    description: str = "Need Python + FastAPI + PostgreSQL backend with Docker.",
    proposal_count: int | None = 8,
    budget_min: Decimal | None = Decimal("2000"),
    budget_max: Decimal | None = Decimal("4000"),
    status: JobStatus = JobStatus.new,
) -> Job:
    now = datetime.now(UTC)
    return Job(
        id=uuid4(),
        user_id=user_id or uuid4(),
        title=title,
        description=description,
        source_url=None,
        budget_type=BudgetType.fixed,
        budget_min=budget_min,
        budget_max=budget_max,
        currency="USD",
        proposal_count=proposal_count,
        client_id=None,
        status=status,
        source_hash="hash-" + uuid4().hex[:8],
        version=1,
        imported_at=now,
        created_at=now,
        updated_at=now,
    )


class FakeJobRepository:
    def __init__(self, jobs: list[Job] | None = None) -> None:
        self._jobs: dict[UUID, Job] = {j.id: j for j in (jobs or [])}

    def add(self, job: Job) -> None:
        self._jobs[job.id] = job

    async def get_by_id(self, job_id: UUID, *, user_id: UUID) -> Job | None:
        job = self._jobs.get(job_id)
        if job is None or job.user_id != user_id:
            return None
        return job

    async def get_by_source_hash(self, source_hash: str, *, user_id: UUID) -> Job | None:
        for j in self._jobs.values():
            if j.user_id == user_id and j.source_hash == source_hash:
                return j
        return None

    async def list_for_user(self, *args: Any, **kwargs: Any) -> tuple[list[Job], int]:
        raise NotImplementedError

    async def create(self, **kwargs: Any) -> Job:
        raise NotImplementedError

    async def update(self, *args: Any, **kwargs: Any) -> Job | None:
        raise NotImplementedError

    async def delete(self, *args: Any, **kwargs: Any) -> bool:
        raise NotImplementedError


class FakeAnalysisRepository:
    def __init__(self) -> None:
        self._by_job: dict[UUID, DomainAnalysis] = {}

    async def get_by_job_id(self, job_id: UUID) -> DomainAnalysis | None:
        return self._by_job.get(job_id)

    async def upsert(self, **kw: Any) -> DomainAnalysis:
        now = datetime.now(UTC)
        existing = self._by_job.get(kw["job_id"])
        analysis = DomainAnalysis(
            id=existing.id if existing else uuid4(),
            job_id=kw["job_id"],
            summary=kw["summary"],
            required_skills=list(kw["required_skills"]),
            preferred_skills=list(kw["preferred_skills"]),
            technologies=list(kw["technologies"]),
            business_domain=kw["business_domain"],
            seniority=kw["seniority"],
            complexity=kw["complexity"],
            estimated_hours_min=kw["estimated_hours_min"],
            estimated_hours_max=kw["estimated_hours_max"],
            budget_assessment=kw["budget_assessment"],
            client_intent=kw["client_intent"],
            hidden_requirements=list(kw["hidden_requirements"]),
            expected_deliverables=list(kw["expected_deliverables"]),
            risks=[
                r if isinstance(r, RiskItem) else RiskItem(**r) for r in kw["risks"]
            ],
            red_flags=list(kw["red_flags"]),
            green_flags=list(kw["green_flags"]),
            questions_to_ask_client=list(kw["questions_to_ask_client"]),
            risk_level=kw["risk_level"],
            communication_required=kw["communication_required"],
            provider=kw["provider"],
            model=kw["model"],
            prompt_version=kw["prompt_version"],
            raw_response=kw["raw_response"],
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self._by_job[kw["job_id"]] = analysis
        return analysis


class FakeScoreRepository:
    def __init__(self) -> None:
        self._by_job: dict[UUID, DomainScore] = {}

    async def get_by_job_id(self, job_id: UUID) -> DomainScore | None:
        return self._by_job.get(job_id)

    async def upsert(self, **kw: Any) -> DomainScore:
        now = datetime.now(UTC)
        existing = self._by_job.get(kw["job_id"])
        score = DomainScore(
            id=existing.id if existing else uuid4(),
            job_id=kw["job_id"],
            analysis_id=kw["analysis_id"],
            score=kw["score"],
            recommendation=kw["recommendation"],
            confidence=kw["confidence"],
            score_breakdown=dict(kw["score_breakdown"]),
            reasoning=kw["reasoning"],
            profile_version=kw["profile_version"],
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self._by_job[kw["job_id"]] = score
        return score


# `field` is re-exported so test modules can `from .factories import ...`
__all__ = [
    "FakeAnalysisRepository",
    "FakeJobRepository",
    "FakeScoreRepository",
    "field",
    "make_job",
    "replace",
]
