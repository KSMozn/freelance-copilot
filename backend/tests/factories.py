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
from app.domain.entities.portfolio import Portfolio


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


def make_portfolio(
    *,
    user_id: UUID | None = None,
    title: str = "Customer 360 Analytics Platform",
    business_domain: str | None = "Enterprise SaaS",
    technologies: list[str] | None = None,
    skills: list[str] | None = None,
    long_description: str = "Built a customer 360 platform on PostgreSQL with FastAPI.",
) -> Portfolio:
    now = datetime.now(UTC)
    return Portfolio(
        id=uuid4(),
        user_id=user_id or uuid4(),
        title=title,
        long_description=long_description,
        short_description="A short blurb.",
        role="Lead Engineer",
        business_domain=business_domain,
        github_url=None,
        live_url=None,
        technologies=technologies or ["PostgreSQL", "Python", "FastAPI"],
        skills=skills or ["PostgreSQL", "Analytics", "Data modeling"],
        features=["Wide customer table", "Materialized views"],
        outcomes=["Cut query times to sub-second"],
        highlight=False,
        created_at=now,
        updated_at=now,
    )


class FakePortfolioRepository:
    def __init__(self, portfolios: list[Portfolio] | None = None) -> None:
        self._items: dict[UUID, Portfolio] = {p.id: p for p in (portfolios or [])}

    def add(self, p: Portfolio) -> None:
        self._items[p.id] = p

    async def create(self, **kw: Any) -> Portfolio:
        portfolio = make_portfolio(
            user_id=kw["user_id"],
            title=kw["title"],
            business_domain=kw.get("business_domain"),
            technologies=list(kw.get("technologies", [])),
            skills=list(kw.get("skills", [])),
            long_description=kw["long_description"],
        )
        portfolio.short_description = kw.get("short_description")
        portfolio.role = kw.get("role")
        portfolio.github_url = kw.get("github_url")
        portfolio.live_url = kw.get("live_url")
        portfolio.features = list(kw.get("features", []))
        portfolio.outcomes = list(kw.get("outcomes", []))
        portfolio.highlight = kw.get("highlight", False)
        self._items[portfolio.id] = portfolio
        return portfolio

    async def get_by_id(self, portfolio_id: UUID, *, user_id: UUID) -> Portfolio | None:
        p = self._items.get(portfolio_id)
        if p is None or p.user_id != user_id:
            return None
        return p

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        search: str | None,
        domain: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Portfolio], int]:
        results = [p for p in self._items.values() if p.user_id == user_id]
        if search:
            s = search.lower()
            results = [
                p
                for p in results
                if s in p.title.lower() or s in p.long_description.lower()
            ]
        if domain:
            d = domain.lower()
            results = [
                p for p in results if p.business_domain and d in p.business_domain.lower()
            ]
        total = len(results)
        return results[offset : offset + limit], total

    async def list_all_for_user(self, user_id: UUID) -> list[Portfolio]:
        return [p for p in self._items.values() if p.user_id == user_id]

    async def update(
        self,
        portfolio_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> Portfolio | None:
        p = self._items.get(portfolio_id)
        if p is None or p.user_id != user_id:
            return None
        for k, v in fields.items():
            setattr(p, k, v)
        return p

    async def delete(self, portfolio_id: UUID, *, user_id: UUID) -> bool:
        p = self._items.get(portfolio_id)
        if p is None or p.user_id != user_id:
            return False
        del self._items[portfolio_id]
        return True


class FakeEmbeddingRepository:
    def __init__(self) -> None:
        self._store: dict[tuple[str, UUID, str], list[float]] = {}

    async def get(
        self, *, owner_type: str, owner_id: UUID, model: str
    ) -> list[float] | None:
        return self._store.get((owner_type, owner_id, model))

    async def upsert(
        self, *, owner_type: str, owner_id: UUID, model: str, vector: list[float]
    ) -> None:
        self._store[(owner_type, owner_id, model)] = list(vector)

    async def get_many(
        self, *, owner_type: str, owner_ids: list[UUID], model: str
    ) -> dict[UUID, list[float]]:
        out: dict[UUID, list[float]] = {}
        for oid in owner_ids:
            v = self._store.get((owner_type, oid, model))
            if v is not None:
                out[oid] = v
        return out

    async def delete(self, *, owner_type: str, owner_id: UUID) -> None:
        for k in list(self._store.keys()):
            if k[0] == owner_type and k[1] == owner_id:
                del self._store[k]


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
    "FakeEmbeddingRepository",
    "FakeJobRepository",
    "FakePortfolioRepository",
    "FakeScoreRepository",
    "field",
    "make_job",
    "make_portfolio",
    "replace",
]
