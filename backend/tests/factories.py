"""Tiny in-memory fakes used by Phase-2 unit tests.

These let us exercise the application layer end-to-end without a Postgres
instance: just a mock AI provider, fake repos, and a real ScoringService.
"""
from __future__ import annotations

from dataclasses import field, replace
from datetime import UTC, datetime


def _as_aware(dt: datetime) -> datetime:
    """Normalize naïve datetimes to UTC so comparisons don't raise.

    The factory-built rows are tz-naïve; the date range coming from the
    real endpoint is tz-aware. Promote the naïve side rather than failing.
    """
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from app.domain.entities.analysis import (
    JobAnalysis as DomainAnalysis,
)
from app.domain.entities.analysis import (
    OpportunityScore as DomainScore,
)
from app.domain.entities.analysis import (
    RiskItem,
)
from app.domain.entities.application import (
    TERMINAL_STATUSES,
    Application,
    ApplicationHistoryEntry,
    ApplicationStatus,
)
from app.domain.entities.job import BudgetType, Job, JobStatus
from app.domain.entities.portfolio import Portfolio
from app.domain.entities.proposal import Milestone, Proposal
from app.domain.entities.resume import Resume


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


def make_application(
    *,
    user_id: UUID | None = None,
    job_id: UUID | None = None,
    status: ApplicationStatus = ApplicationStatus.applied,
    snapshot: dict[str, Any] | None = None,
    applied_at: datetime | None = None,
    viewed_at: datetime | None = None,
    interview_at: datetime | None = None,
    offer_at: datetime | None = None,
    won_at: datetime | None = None,
    rejected_at: datetime | None = None,
    withdrawn_at: datetime | None = None,
    completed_at: datetime | None = None,
    contract_amount: object | None = None,
    created_at: datetime | None = None,
) -> Application:
    now = datetime.now(UTC)
    return Application(
        id=uuid4(),
        user_id=user_id or uuid4(),
        job_id=job_id or uuid4(),
        status=status,
        applied_at=applied_at if applied_at is not None else (now if status != ApplicationStatus.draft else None),
        viewed_at=viewed_at,
        interview_at=interview_at,
        offer_at=offer_at,
        won_at=won_at,
        rejected_at=rejected_at,
        withdrawn_at=withdrawn_at,
        completed_at=completed_at,
        contract_amount=contract_amount,  # type: ignore[arg-type]
        snapshot=snapshot,
        created_at=created_at or now,
        updated_at=created_at or now,
    )


def make_resume(
    *,
    user_id: UUID | None = None,
    title: str = "AI / LLM Platform Resume",
    target_role: str | None = "AI / Backend Engineer",
    summary: str | None = "RAG + FastAPI + PostgreSQL backend engineer.",
    seniority_level: str | None = "senior",
    primary_skills: list[str] | None = None,
    secondary_skills: list[str] | None = None,
    industries: list[str] | None = None,
    domains: list[str] | None = None,
    achievements: list[str] | None = None,
    project_highlights: list[str] | None = None,
    keywords: list[str] | None = None,
    notes: str | None = None,
) -> Resume:
    now = datetime.now(UTC)
    return Resume(
        id=uuid4(),
        user_id=user_id or uuid4(),
        title=title,
        target_role=target_role,
        summary=summary,
        seniority_level=seniority_level,
        primary_skills=primary_skills or ["Python", "FastAPI", "RAG", "OpenAI"],
        secondary_skills=secondary_skills or ["PostgreSQL", "Docker"],
        industries=industries or ["AI SaaS"],
        domains=domains or ["AI SaaS"],
        achievements=achievements or ["Shipped a production RAG platform."],
        project_highlights=project_highlights or ["On-prem RAG over enterprise docs."],
        keywords=keywords or ["RAG", "LLM", "vector search"],
        notes=notes,
        created_at=now,
        updated_at=now,
    )


class FakeResumeRepository:
    def __init__(self, resumes: list[Resume] | None = None) -> None:
        self._items: dict[UUID, Resume] = {r.id: r for r in (resumes or [])}

    def add(self, r: Resume) -> None:
        self._items[r.id] = r

    async def create(self, **kw: Any) -> Resume:
        resume = make_resume(
            user_id=kw["user_id"],
            title=kw["title"],
            target_role=kw.get("target_role"),
            summary=kw.get("summary"),
            seniority_level=kw.get("seniority_level"),
            primary_skills=list(kw.get("primary_skills", [])),
            secondary_skills=list(kw.get("secondary_skills", [])),
            industries=list(kw.get("industries", [])),
            domains=list(kw.get("domains", [])),
            achievements=list(kw.get("achievements", [])),
            project_highlights=list(kw.get("project_highlights", [])),
            keywords=list(kw.get("keywords", [])),
            notes=kw.get("notes"),
        )
        self._items[resume.id] = resume
        return resume

    async def get_by_id(self, resume_id: UUID, *, user_id: UUID) -> Resume | None:
        r = self._items.get(resume_id)
        if r is None or r.user_id != user_id:
            return None
        return r

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        search: str | None,
        domain: str | None,
        skill: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Resume], int]:
        results = [r for r in self._items.values() if r.user_id == user_id]
        if search:
            s = search.lower()
            results = [
                r
                for r in results
                if s in r.title.lower()
                or (r.target_role and s in r.target_role.lower())
                or (r.summary and s in r.summary.lower())
            ]
        if domain:
            results = [r for r in results if domain in r.domains]
        if skill:
            results = [
                r
                for r in results
                if skill in r.primary_skills or skill in r.secondary_skills
            ]
        total = len(results)
        return results[offset : offset + limit], total

    async def list_all_for_user(self, user_id: UUID) -> list[Resume]:
        return [r for r in self._items.values() if r.user_id == user_id]

    async def update(
        self,
        resume_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> Resume | None:
        r = self._items.get(resume_id)
        if r is None or r.user_id != user_id:
            return None
        for k, v in fields.items():
            setattr(r, k, v)
        return r

    async def delete(self, resume_id: UUID, *, user_id: UUID) -> bool:
        r = self._items.get(resume_id)
        if r is None or r.user_id != user_id:
            return False
        del self._items[resume_id]
        return True


class FakeProposalRepository:
    def __init__(self, proposals: list[Proposal] | None = None) -> None:
        self._items: dict[UUID, Proposal] = {p.id: p for p in (proposals or [])}

    async def create(self, **kw: Any) -> Proposal:
        now = datetime.now(UTC)
        milestones = list(kw.get("milestones") or [])
        proposal = Proposal(
            id=uuid4(),
            user_id=kw["user_id"],
            job_id=kw["job_id"],
            resume_id=kw.get("resume_id"),
            portfolio_ids=list(kw.get("portfolio_ids") or []),
            title=kw.get("title"),
            body=kw["body"],
            short_body=kw.get("short_body"),
            questions=list(kw.get("questions") or []),
            milestones=[
                m if isinstance(m, Milestone) else Milestone(**m) for m in milestones
            ],
            delivery_approach=list(kw.get("delivery_approach") or []),
            risk_notes=list(kw.get("risk_notes") or []),
            quality_score=kw.get("quality_score"),
            quality_breakdown=kw.get("quality_breakdown"),
            quality_warnings=list(kw.get("quality_warnings") or []),
            prompt_version=kw.get("prompt_version"),
            model_provider=kw.get("model_provider"),
            model_name=kw.get("model_name"),
            raw_response=kw.get("raw_response"),
            created_at=now,
            updated_at=now,
        )
        self._items[proposal.id] = proposal
        return proposal

    async def get_by_id(self, proposal_id: UUID, *, user_id: UUID) -> Proposal | None:
        p = self._items.get(proposal_id)
        if p is None or p.user_id != user_id:
            return None
        return p

    async def list_by_job_id(self, job_id: UUID, *, user_id: UUID) -> list[Proposal]:
        return sorted(
            (
                p
                for p in self._items.values()
                if p.user_id == user_id and p.job_id == job_id
            ),
            key=lambda p: p.created_at or datetime.now(UTC),
            reverse=True,
        )

    async def get_latest_by_job_id(
        self, job_id: UUID, *, user_id: UUID
    ) -> Proposal | None:
        items = await self.list_by_job_id(job_id, user_id=user_id)
        return items[0] if items else None

    async def update(
        self,
        proposal_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> Proposal | None:
        p = self._items.get(proposal_id)
        if p is None or p.user_id != user_id:
            return None
        for k, v in fields.items():
            if k == "milestones" and isinstance(v, list):
                p.milestones = [m if isinstance(m, Milestone) else Milestone(**m) for m in v]
            else:
                setattr(p, k, v)
        p.updated_at = datetime.now(UTC)
        return p

    async def delete(self, proposal_id: UUID, *, user_id: UUID) -> bool:
        p = self._items.get(proposal_id)
        if p is None or p.user_id != user_id:
            return False
        del self._items[proposal_id]
        return True


class FakeApplicationRepository:
    def __init__(self, applications: list[Application] | None = None) -> None:
        self._items: dict[UUID, Application] = {a.id: a for a in (applications or [])}

    async def create(self, **kw: Any) -> Application:
        now = datetime.now(UTC)
        app = Application(
            id=uuid4(),
            user_id=kw["user_id"],
            job_id=kw["job_id"],
            proposal_id=kw.get("proposal_id"),
            resume_id=kw.get("resume_id"),
            portfolio_ids=list(kw.get("portfolio_ids") or []),
            status=kw["status"],
            applied_at=kw.get("applied_at"),
            snapshot=kw.get("snapshot"),
            created_at=now,
            updated_at=now,
        )
        self._items[app.id] = app
        return app

    async def get_by_id(self, application_id: UUID, *, user_id: UUID) -> Application | None:
        a = self._items.get(application_id)
        if a is None or a.user_id != user_id:
            return None
        return a

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        status: ApplicationStatus | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Application], int]:
        results = [a for a in self._items.values() if a.user_id == user_id]
        if status is not None:
            results = [a for a in results if a.status == status]
        # In-memory search ignores join-based "search" so tests can opt in
        # via direct repo state.
        if search:
            s = search.lower()
            snapshot_match = lambda a: bool(  # noqa: E731
                a.snapshot and a.snapshot.get("job", {}).get("title")
                and s in str(a.snapshot["job"]["title"]).lower()
            )
            results = [a for a in results if snapshot_match(a)]
        total = len(results)
        return results[offset : offset + limit], total

    async def find_active_for_job(
        self, *, user_id: UUID, job_id: UUID
    ) -> Application | None:
        for a in self._items.values():
            if a.user_id != user_id or a.job_id != job_id:
                continue
            if a.status in TERMINAL_STATUSES:
                continue
            return a
        return None

    async def update(
        self,
        application_id: UUID,
        *,
        user_id: UUID,
        fields: dict[str, object],
    ) -> Application | None:
        a = self._items.get(application_id)
        if a is None or a.user_id != user_id:
            return None
        for k, v in fields.items():
            if k == "status":
                a.status = v if isinstance(v, ApplicationStatus) else ApplicationStatus(v)
            else:
                setattr(a, k, v)
        a.updated_at = datetime.now(UTC)
        return a

    async def delete(self, application_id: UUID, *, user_id: UUID) -> bool:
        a = self._items.get(application_id)
        if a is None or a.user_id != user_id:
            return False
        del self._items[application_id]
        return True

    async def list_for_analytics(
        self,
        user_id: UUID,
        *,
        from_date=None,
        to_date=None,
    ) -> list[Application]:
        results = [a for a in self._items.values() if a.user_id == user_id]
        if from_date is not None:
            results = [
                a for a in results
                if a.created_at and _as_aware(a.created_at) >= _as_aware(from_date)
            ]
        if to_date is not None:
            results = [
                a for a in results
                if a.created_at and _as_aware(a.created_at) <= _as_aware(to_date)
            ]
        return results


class FakeApplicationHistoryRepository:
    def __init__(self) -> None:
        self._items: list[ApplicationHistoryEntry] = []

    async def create(
        self,
        *,
        application_id: UUID,
        user_id: UUID | None,
        from_status: str | None,
        to_status: str,
        note: str | None,
    ) -> ApplicationHistoryEntry:
        entry = ApplicationHistoryEntry(
            id=uuid4(),
            application_id=application_id,
            user_id=user_id,
            from_status=from_status,
            to_status=to_status,
            note=note,
            created_at=datetime.now(UTC),
        )
        self._items.append(entry)
        return entry

    async def list_for_application(
        self, application_id: UUID, *, user_id: UUID
    ) -> list[ApplicationHistoryEntry]:
        return [
            h
            for h in self._items
            if h.application_id == application_id and (h.user_id is None or h.user_id == user_id)
        ]

    async def list_recent_for_user(
        self,
        user_id: UUID,
        *,
        limit: int,
    ) -> list[ApplicationHistoryEntry]:
        results = [h for h in self._items if h.user_id == user_id]
        results.sort(key=lambda h: h.created_at, reverse=True)
        return results[:limit]


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
    "FakeApplicationHistoryRepository",
    "FakeApplicationRepository",
    "FakeEmbeddingRepository",
    "FakeJobRepository",
    "FakePortfolioRepository",
    "FakeProposalRepository",
    "FakeResumeRepository",
    "FakeScoreRepository",
    "field",
    "make_application",
    "make_job",
    "make_portfolio",
    "make_resume",
    "replace",
]
