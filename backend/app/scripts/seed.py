"""Insert a demo user, a demo job, and the Phase-3 portfolio set.

Idempotent: re-running does nothing once the rows exist. Portfolio embeddings
are generated via the currently-configured embedding provider (mock by
default).

Run inside the backend container:

    docker compose exec backend python -m app.scripts.seed
"""
from __future__ import annotations

import asyncio
import hashlib
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import text

from app.application.dto.application_dto import (
    ApplicationDetailsUpdate,
    CreateFromProposalRequest,
    StatusUpdateRequest,
)
from app.application.dto.portfolio_dto import PortfolioCreate
from app.application.dto.resume_dto import ResumeCreate
from app.application.services.application_service import ApplicationService
from app.application.services.job_analysis_service import JobAnalysisService
from app.application.services.portfolio_matching_service import PortfolioMatchingService
from app.application.services.portfolio_service import PortfolioService
from app.application.services.proposal_generation_service import (
    ProposalGenerationService,
)
from app.application.services.proposal_review_service import ProposalReviewService
from app.application.services.resume_recommendation_service import (
    ResumeRecommendationService,
)
from app.application.services.resume_service import ResumeService
from app.application.services.scoring_service import ScoringService
from app.domain.exceptions import AlreadyExistsError
from app.domain.profiles.freelancer_profile import DEFAULT_FREELANCER_PROFILE
from app.infrastructure.ai.factory import build_ai_provider
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.domain.entities.job import BudgetType, JobStatus
from app.infrastructure.ai.embedding_factory import build_embedding_provider
from app.infrastructure.db.repositories.sqlalchemy_embedding_repository import (
    SQLAlchemyEmbeddingRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_job_repository import (
    SQLAlchemyJobRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_analysis_repository import (
    SQLAlchemyJobAnalysisRepository,
    SQLAlchemyOpportunityScoreRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_application_repository import (
    SQLAlchemyApplicationHistoryRepository,
    SQLAlchemyApplicationRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_portfolio_repository import (
    SQLAlchemyPortfolioRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_proposal_repository import (
    SQLAlchemyProposalRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_resume_repository import (
    SQLAlchemyResumeRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo-password-123"
DEMO_NAME = "Demo User"

DEMO_JOB_TITLE = "Build a FastAPI + Postgres backend with RAG over PDF documents"
DEMO_JOB_DESCRIPTION = """We're a small AI SaaS company building an internal \
document-management tool for enterprise customers. We need an experienced \
backend engineer to design and ship the first version.

Scope:
- Python 3.13 + FastAPI service with async SQLAlchemy and PostgreSQL (pgvector).
- A small RAG pipeline: ingest PDFs, chunk + embed via OpenAI, store in pgvector, \
  retrieve top-K on query.
- Clean REST API with JWT auth (we already have a React/TypeScript front end).
- Docker + docker-compose for local dev, basic GitHub Actions CI.
- Deployment instructions for our AWS account (ECS + RDS).

Nice to have:
- Prior experience with LLM evaluation / prompt versioning.
- Familiarity with Claude as well as OpenAI.

Engagement:
- 4–6 weeks, starting in two weeks.
- Long-term collaboration possible if this goes well.
- Async-first, with a 30-minute weekly sync on Tuesdays.

Deliverables:
- Working backend repo with tests.
- Deployment guide.
- Hand-over session.

If you've built something similar before, please share links. Looking for a \
senior engineer who can work independently and push back on under-specified \
requirements."""


DEMO_PORTFOLIOS: list[dict[str, Any]] = [
    {
        "title": "Customer 360 Analytics Platform",
        "short_description": (
            "Unified customer view + analytics on top of a PostgreSQL warehouse."
        ),
        "long_description": (
            "Designed and shipped a customer-360 platform for an enterprise SaaS "
            "team: ingestion from product, billing, and support sources into a "
            "PostgreSQL warehouse, modeled into wide customer + event tables, "
            "exposed via materialized views and a FastAPI read-API powering "
            "internal dashboards. Took the project from a single Looker tile to "
            "an opinionated platform the success team relies on daily."
        ),
        "role": "Lead Backend Engineer",
        "business_domain": "Enterprise SaaS",
        "github_url": None,
        "live_url": None,
        "technologies": [
            "PostgreSQL",
            "Python",
            "FastAPI",
            "SQLAlchemy",
            "dbt",
            "Airflow",
        ],
        "skills": [
            "PostgreSQL",
            "Data modeling",
            "Analytics",
            "FastAPI",
            "Materialized views",
            "ETL",
        ],
        "features": [
            "Wide customer table with rolling 90-day activity",
            "Materialized customer timeline for instant lookup",
            "Self-serve segment builder over the warehouse",
        ],
        "outcomes": [
            "Cut analytics queries from minutes to sub-second p95",
            "Replaced 4 ad-hoc spreadsheets with a single source of truth",
        ],
        "highlight": True,
    },
    {
        "title": "LinkedIn Data Portability POC",
        "short_description": (
            "OAuth + LinkedIn API integration producing a compliance-safe CSV export."
        ),
        "long_description": (
            "Built a proof-of-concept for a GDPR-style data portability flow: "
            "user authenticates via LinkedIn OAuth, the backend pulls allowed "
            "profile and activity surfaces, normalizes them, and produces a "
            "downloadable CSV. The harder half was compliance-aware design — "
            "scope minimization, rate-limit-friendly retries, and a clear "
            "consent trail."
        ),
        "role": "Backend Engineer",
        "business_domain": "Government",
        "github_url": None,
        "live_url": None,
        "technologies": ["Python", "OAuth2", "LinkedIn API", "FastAPI", "PostgreSQL"],
        "skills": [
            "OAuth",
            "API integration",
            "Python",
            "CSV export",
            "Compliance",
            "Rate limiting",
        ],
        "features": [
            "OAuth2 PKCE flow with scope minimization",
            "Resumable export over flaky network conditions",
            "Audit trail of every API call made on the user's behalf",
        ],
        "outcomes": [
            "Cleared internal legal review on first pass",
            "Reused as the template for two later portability flows",
        ],
        "highlight": False,
    },
    {
        "title": "AI Document Q&A — Arabic RAG Platform",
        "short_description": (
            "On-prem RAG over Arabic enterprise documents with row-level access control."
        ),
        "long_description": (
            "Designed and built an on-prem RAG platform for an enterprise "
            "customer with Arabic-first content: PDF + Office ingestion, "
            "language-aware chunking, hybrid retrieval combining pgvector "
            "embeddings with BM25, and an LLM answer step using OpenAI and "
            "Claude with strict row-level access control so a user only ever "
            "sees content they're cleared to see. Shipped a Docker-only "
            "deployment so the customer ran it inside their own network."
        ),
        "role": "AI / Backend Architect",
        "business_domain": "Document Management",
        "github_url": None,
        "live_url": None,
        "technologies": [
            "FastAPI",
            "Python",
            "PostgreSQL",
            "pgvector",
            "OpenAI",
            "Claude",
            "Docker",
            "RAG",
            "LLM",
        ],
        "skills": [
            "FastAPI",
            "RAG",
            "LLM",
            "Arabic NLP",
            "Access control",
            "On-prem deployment",
            "Prompt engineering",
        ],
        "features": [
            "Hybrid retrieval (pgvector + BM25) with re-ranking",
            "Per-document ACL enforced at retrieval time, not just response",
            "Provider abstraction over OpenAI + Claude with prompt versioning",
            "Air-gapped deployment via Docker images",
        ],
        "outcomes": [
            "Reached production with 1k+ Arabic documents ingested",
            "Cut analyst lookup time from minutes to seconds",
        ],
        "highlight": True,
    },
    {
        "title": "Retool Marketplace Admin Panel",
        "short_description": (
            "Admin dashboards + workflow automation for a B2B marketplace."
        ),
        "long_description": (
            "Built a Retool-based operator console for a marketplace startup: "
            "supplier onboarding flows, dynamic pricing logic, product catalog "
            "edits, dispute handling, and a PostgreSQL audit log for every "
            "operator action. Replaced a Google-Sheets-and-Slack process with "
            "a real workflow."
        ),
        "role": "Full-stack Engineer",
        "business_domain": "Enterprise SaaS",
        "github_url": None,
        "live_url": None,
        "technologies": ["Retool", "PostgreSQL", "Node.js", "REST", "Python"],
        "skills": [
            "Admin dashboards",
            "Pricing logic",
            "Workflow automation",
            "PostgreSQL",
            "Supplier management",
            "Product management",
        ],
        "features": [
            "Supplier onboarding wizard with verification checks",
            "Dynamic pricing engine driven by SQL-backed rules",
            "Operator audit log — every change tied to a user + reason",
        ],
        "outcomes": [
            "Reduced operator response time on disputes by ~60%",
            "Made the on-call rotation calmer — no more midnight DB edits",
        ],
        "highlight": False,
    },
]


DEMO_RESUMES: list[dict[str, Any]] = [
    {
        "title": "AI / LLM Platform Resume",
        "target_role": "AI / Backend Engineer",
        "summary": (
            "Senior engineer who has shipped production RAG systems on top of "
            "FastAPI + PostgreSQL + pgvector, with OpenAI and Claude in the loop. "
            "Comfortable with prompt versioning, evaluation, and access control."
        ),
        "seniority_level": "senior",
        "primary_skills": [
            "Python",
            "FastAPI",
            "RAG",
            "OpenAI",
            "Claude",
            "LLM",
            "PostgreSQL",
            "pgvector",
        ],
        "secondary_skills": ["Docker", "Kubernetes", "AWS", "Prompt engineering"],
        "industries": ["AI SaaS", "Enterprise SaaS"],
        "domains": ["AI SaaS", "Document Management"],
        "achievements": [
            "Shipped Arabic-first RAG platform with row-level ACLs to production.",
            "Cut analyst lookup time from minutes to seconds via hybrid retrieval.",
        ],
        "project_highlights": [
            "On-prem RAG over enterprise documents (FastAPI + pgvector + OpenAI).",
            "Provider abstraction over OpenAI + Claude with prompt versioning.",
        ],
        "keywords": [
            "RAG",
            "document Q&A",
            "enterprise AI",
            "vector search",
            "LLM evaluation",
        ],
        "notes": "Lead with AI/RAG experience when the job mentions document Q&A.",
    },
    {
        "title": "Python Backend Resume",
        "target_role": "Senior Backend Engineer",
        "summary": (
            "Backend engineer focused on Python services, REST + async APIs, "
            "PostgreSQL data modeling, and Docker-based deployments."
        ),
        "seniority_level": "senior",
        "primary_skills": [
            "Python",
            "FastAPI",
            "PostgreSQL",
            "SQLAlchemy",
            "Docker",
            "REST",
            "asyncio",
        ],
        "secondary_skills": ["Redis", "Celery", "AWS", "CI/CD", "Testing"],
        "industries": ["Enterprise SaaS", "FinTech", "Analytics"],
        "domains": ["Enterprise SaaS", "Data Platforms"],
        "achievements": [
            "Built data-ingestion APIs handling 10k events/min on a single node.",
            "Cut p95 latency on a core endpoint by 4x via async + query rewrites.",
        ],
        "project_highlights": [
            "FastAPI service with async SQLAlchemy and pgvector retrieval.",
            "PostgreSQL schema modeling and materialized-view-driven analytics.",
        ],
        "keywords": ["FastAPI", "PostgreSQL", "Docker", "data processing", "APIs"],
        "notes": "Default fallback for any Python-heavy backend job.",
    },
    {
        "title": "Full Stack SaaS Resume",
        "target_role": "Full-stack Engineer",
        "summary": (
            "End-to-end SaaS engineer: React/TypeScript front ends, Node.js and "
            "FastAPI back ends, PostgreSQL. Comfortable owning an MVP from "
            "auth to deployment."
        ),
        "seniority_level": "senior",
        "primary_skills": [
            "React",
            "TypeScript",
            "Node.js",
            "FastAPI",
            "PostgreSQL",
            "Tailwind",
        ],
        "secondary_skills": ["GraphQL", "Vite", "Stripe", "Auth0"],
        "industries": ["Enterprise SaaS", "Startups"],
        "domains": ["Enterprise SaaS"],
        "achievements": [
            "Took a B2B SaaS MVP from zero to first paying customer in 8 weeks.",
            "Migrated a Stripe billing flow with zero downtime.",
        ],
        "project_highlights": [
            "React + Vite admin console powered by a FastAPI back end.",
            "Multi-tenant PostgreSQL schema with row-level isolation.",
        ],
        "keywords": ["SaaS MVP", "full stack", "React", "TypeScript", "Node.js"],
        "notes": "Use for jobs spanning both frontend and backend.",
    },
    {
        "title": "Architecture / Technical Audit Resume",
        "target_role": "Software Architect / Technical Auditor",
        "summary": (
            "Architect who reviews codebases, identifies systemic risk, and "
            "produces actionable plans. Comfortable across cloud platforms, "
            "stress-testing scalability assumptions, and pairing with teams."
        ),
        "seniority_level": "staff",
        "primary_skills": [
            "System design",
            "Scalability",
            "Cloud architecture",
            "Code review",
            "Production readiness",
        ],
        "secondary_skills": ["AWS", "GCP", "PostgreSQL", "Kubernetes", "Observability"],
        "industries": ["Enterprise SaaS", "FinTech", "Government"],
        "domains": ["Cloud Platforms", "Enterprise SaaS"],
        "achievements": [
            "Audited a Series-B platform and identified the cause of weekly outages.",
            "Defined a multi-region cutover plan with rollback at each step.",
        ],
        "project_highlights": [
            "Architecture review of a regulated FinTech data pipeline.",
            "Production-readiness checklist adopted by three engineering teams.",
        ],
        "keywords": [
            "architecture review",
            "technical audit",
            "scalability",
            "production readiness",
            "code review",
        ],
        "notes": "Lead with audit framing when the job mentions architecture or compliance.",
    },
    {
        "title": "Engineering Manager Resume",
        "target_role": "Engineering Manager",
        "summary": (
            "Player-coach EM who has led distributed product teams and platform "
            "teams. Comfortable with engineering strategy, mentoring, and "
            "delivery rituals — without losing the ability to read code."
        ),
        "seniority_level": "lead",
        "primary_skills": [
            "Engineering strategy",
            "Delivery leadership",
            "Mentoring",
            "Distributed teams",
            "Platform teams",
        ],
        "secondary_skills": ["Hiring", "OKR planning", "Roadmap design", "Postmortems"],
        "industries": ["Enterprise SaaS", "Startups"],
        "domains": ["Enterprise SaaS"],
        "achievements": [
            "Built and led a fully-remote platform team across 4 time zones.",
            "Halved time-to-merge by introducing a calmer review process.",
        ],
        "project_highlights": [
            "Stood up a platform team and shipped 3 paved roads in one quarter.",
            "Rebuilt the on-call rotation around blameless postmortems.",
        ],
        "keywords": [
            "engineering manager",
            "delivery leadership",
            "platform team",
            "mentoring",
            "distributed teams",
        ],
        "notes": "Avoid using when the role is clearly individual-contributor.",
    },
]


# Phase-7 analytics demo data ---------------------------------------------------

_ANALYTICS_DEMO_SPECS: list[dict[str, Any]] = [
    {
        "title": "FastAPI + PostgreSQL backend for an AI SaaS internal tool",
        "description": (
            "Looking for an experienced backend engineer to build a small FastAPI + "
            "PostgreSQL service. The team is an AI SaaS startup — bonus if you've "
            "shipped OpenAI integrations before. Docker-based deploy."
        ),
        "budget": (Decimal("2500"), Decimal("4000"), "USD", "fixed"),
        "proposal_count": 14,
        "target_status": "completed",
        "contract_amount": Decimal("3800.00"),
        "days_ago": 145,
        "transitions": [
            ("viewed", 1), ("interview", 2), ("offer", 5), ("won", 7), ("completed", 35),
        ],
    },
    {
        "title": "RAG over enterprise document set (Python + pgvector + OpenAI)",
        "description": (
            "AI SaaS company needs a senior engineer to design an on-prem RAG "
            "pipeline over enterprise PDFs. Python, pgvector, OpenAI. Document "
            "Management vertical."
        ),
        "budget": (Decimal("4000"), Decimal("6000"), "USD", "fixed"),
        "proposal_count": 9,
        "target_status": "won",
        "contract_amount": Decimal("5200.00"),
        "days_ago": 60,
        "transitions": [("viewed", 1), ("interview", 3), ("offer", 5), ("won", 9)],
    },
    {
        "title": "React + TypeScript marketing site for a FinTech",
        "description": (
            "FinTech startup needs a React + TypeScript marketing site with Stripe "
            "checkout integration. Smaller scope, fixed budget."
        ),
        "budget": (Decimal("800"), Decimal("1200"), "USD", "fixed"),
        "proposal_count": 28,
        "target_status": "rejected",
        "contract_amount": None,
        "days_ago": 90,
        "transitions": [("viewed", 2), ("rejected", 6)],
    },
    {
        "title": "Document Management workflow on AWS for a Government client",
        "description": (
            "Government agency needs a Document Management workflow built on AWS + "
            "Python. Compliance-aware, audit trail required."
        ),
        "budget": (Decimal("5000"), Decimal("8000"), "USD", "fixed"),
        "proposal_count": 6,
        "target_status": "interview",
        "contract_amount": None,
        "days_ago": 12,
        "transitions": [("viewed", 1), ("interview", 5)],
    },
    {
        "title": "Marketplace backend — supplier onboarding + pricing logic",
        "description": (
            "Marketplace startup needs PostgreSQL + Node.js backend with admin "
            "dashboards. Pricing rules engine. Long-term collaboration possible."
        ),
        "budget": (Decimal("3000"), Decimal("5000"), "USD", "fixed"),
        "proposal_count": 18,
        "target_status": "offer",
        "contract_amount": None,
        "days_ago": 22,
        "transitions": [("viewed", 1), ("interview", 4), ("offer", 8)],
    },
    {
        "title": "Analytics dashboard over Snowflake (Python + SQL)",
        "description": (
            "Analytics team needs Python + SQL work on top of a Snowflake warehouse. "
            "Build a small dashboard layer with REST API. Data Platforms domain."
        ),
        "budget": (Decimal("1500"), Decimal("2500"), "USD", "fixed"),
        "proposal_count": 22,
        "target_status": "viewed",
        "contract_amount": None,
        "days_ago": 7,
        "transitions": [("viewed", 3)],
    },
    {
        "title": "Cloud architecture review for an Enterprise SaaS platform",
        "description": (
            "Enterprise SaaS needs a one-off architecture review of their Kubernetes "
            "+ AWS deployment. Focus on cost and reliability. Cloud Platforms vertical."
        ),
        "budget": (Decimal("2000"), Decimal("3500"), "USD", "fixed"),
        "proposal_count": 11,
        "target_status": "applied",
        "contract_amount": None,
        "days_ago": 3,
        "transitions": [],
    },
    {
        "title": "Stripe + Supabase MVP for a Marketing Ops startup",
        "description": (
            "Marketing Ops startup wants a Stripe + Supabase MVP shipped in a month. "
            "React frontend, Node.js backend, OAuth login."
        ),
        "budget": (Decimal("3500"), Decimal("5500"), "USD", "fixed"),
        "proposal_count": 16,
        "target_status": "withdrawn",
        "contract_amount": None,
        "days_ago": 40,
        "transitions": [("viewed", 1), ("interview", 3), ("withdrawn", 8)],
    },
    {
        "title": "LangChain + Claude evaluation harness",
        "description": (
            "AI SaaS team needs an evaluation harness for LangChain + Claude pipelines. "
            "Python, Docker, REST API for kicking off eval runs."
        ),
        "budget": (Decimal("1200"), Decimal("1800"), "USD", "fixed"),
        "proposal_count": 4,
        "target_status": "completed",
        "contract_amount": Decimal("1750.00"),
        "days_ago": 200,
        "transitions": [("viewed", 1), ("interview", 2), ("offer", 4), ("won", 6), ("completed", 28)],
    },
    {
        "title": "Internal tooling: PostgreSQL + Python data sync",
        "description": (
            "Enterprise SaaS team needs a Python + PostgreSQL data-sync job between "
            "two internal systems. Docker-based, REST API endpoints."
        ),
        "budget": (Decimal("400"), Decimal("700"), "USD", "fixed"),
        "proposal_count": 8,
        "target_status": "won",
        "contract_amount": Decimal("650.00"),
        "days_ago": 18,
        "transitions": [("viewed", 1), ("interview", 2), ("offer", 4), ("won", 6)],
    },
    {
        "title": "Quick fix: small WordPress data export",
        "description": (
            "Small one-off project to export some data from a WordPress site. "
            "Looking for the cheapest option."
        ),
        "budget": (Decimal("75"), Decimal("150"), "USD", "fixed"),
        "proposal_count": 41,
        "target_status": "rejected",
        "contract_amount": None,
        "days_ago": 55,
        "transitions": [("rejected", 2)],
    },
]


def _hash_demo_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def _seed_analytics_application(
    *,
    session: Any,
    user_id: Any,
    spec: dict[str, Any],
    jobs_repo: SQLAlchemyJobRepository,
    analyzer: "JobAnalysisService",
    generator: "ProposalGenerationService",
    app_service: "ApplicationService",
) -> None:
    """Create one demo application end-to-end and back-date its timestamps.

    The flow is the same as the real user path (analyze → propose → apply)
    so the snapshot stays representative — only the timestamps are nudged.
    """
    bmin, bmax, currency, budget_type = spec["budget"]
    source_hash = _hash_demo_text(spec["description"])
    job = await jobs_repo.create(
        user_id=user_id,
        title=spec["title"],
        description=spec["description"],
        source_hash=source_hash,
        source_url=None,
        budget_type=BudgetType(budget_type),
        budget_min=bmin,
        budget_max=bmax,
        currency=currency,
        proposal_count=spec["proposal_count"],
        status=JobStatus.new,
    )
    await analyzer.analyze(user_id=user_id, job_id=job.id)
    proposal = await generator.generate(user_id=user_id, job_id=job.id)
    application = await app_service.create_from_proposal(
        user_id=user_id,
        proposal_id=proposal.id,
        payload=CreateFromProposalRequest(status="applied", note="Seeded for analytics demo."),
    )

    # Walk through the configured transitions (already-validated state machine).
    for to_status, _ in spec["transitions"]:
        await app_service.update_status(
            user_id=user_id,
            application_id=application.id,
            payload=StatusUpdateRequest(to_status=to_status),
        )

    # Patch the contract amount on terminal-money apps.
    if spec.get("contract_amount") is not None:
        await app_service.update_details(
            user_id=user_id,
            application_id=application.id,
            payload=ApplicationDetailsUpdate(contract_amount=spec["contract_amount"]),
        )

    # Back-date timestamps so the analytics charts span a few months.
    days_ago = int(spec["days_ago"])
    base = datetime.now(UTC) - timedelta(days=days_ago)
    timestamp_updates: dict[str, datetime] = {
        "created_at": base,
        "updated_at": base,
        "applied_at": base,
    }
    for to_status, day_offset in spec["transitions"]:
        ts_col = {
            "viewed": "viewed_at",
            "interview": "interview_at",
            "offer": "offer_at",
            "won": "won_at",
            "rejected": "rejected_at",
            "withdrawn": "withdrawn_at",
            "completed": "completed_at",
        }.get(to_status)
        if ts_col is None:
            continue
        timestamp_updates[ts_col] = base + timedelta(days=day_offset)

    # Issue a single UPDATE so the application's timestamps reflect the
    # back-dated schedule. Analytics groups revenue by month using these.
    set_clauses = ", ".join(f"{col} = :{col}" for col in timestamp_updates)
    params: dict[str, Any] = {"id": str(application.id), **{
        col: ts for col, ts in timestamp_updates.items()
    }}
    await session.execute(
        text(f"UPDATE applications SET {set_clauses} WHERE id = :id"), params
    )

    # Also back-date the initial history entry so "recent activity" stays
    # interleaved across the spec'd days, not all at "now".
    await session.execute(
        text(
            "UPDATE application_history SET created_at = :created_at "
            "WHERE application_id = :id AND from_status IS NULL"
        ),
        {"id": str(application.id), "created_at": base},
    )
    await session.commit()

    print(
        f"Seeded analytics demo: {spec['title']} "
        f"(target={spec['target_status']}, days_ago={days_ago})"
    )


async def main() -> None:
    settings = get_settings()
    embedding_provider = build_embedding_provider(settings)

    async with AsyncSessionLocal() as session:
        users = SQLAlchemyUserRepository(session)
        existing_user = await users.get_by_email(DEMO_EMAIL)
        if existing_user:
            print(f"User already exists: {DEMO_EMAIL}")
            user = existing_user
        else:
            user = await users.create(
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                full_name=DEMO_NAME,
            )
            print(f"Created user {user.email} ({user.id})")
            print(f"Password: {DEMO_PASSWORD}")

        jobs = SQLAlchemyJobRepository(session)
        normalized = re.sub(r"\s+", " ", DEMO_JOB_DESCRIPTION).strip().lower()
        source_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        existing_job = await jobs.get_by_source_hash(source_hash, user_id=user.id)
        if existing_job:
            print(f"Demo job already exists: {existing_job.id}")
        else:
            job = await jobs.create(
                user_id=user.id,
                title=DEMO_JOB_TITLE,
                description=DEMO_JOB_DESCRIPTION,
                source_hash=source_hash,
                source_url=None,
                budget_type=BudgetType.fixed,
                budget_min=Decimal("3000"),
                budget_max=Decimal("5000"),
                currency="USD",
                proposal_count=12,
                status=JobStatus.new,
            )
            print(f"Created demo job {job.id}: {job.title}")

        portfolio_service = PortfolioService(
            portfolio_repo=SQLAlchemyPortfolioRepository(session),
            embedding_repo=SQLAlchemyEmbeddingRepository(session),
            embedding_provider=embedding_provider,
        )
        existing_titles = {
            p.title
            for p in (await SQLAlchemyPortfolioRepository(session).list_all_for_user(user.id))
        }
        for spec in DEMO_PORTFOLIOS:
            if spec["title"] in existing_titles:
                print(f"Portfolio already exists: {spec['title']}")
                continue
            await portfolio_service.create(user.id, PortfolioCreate(**spec))
            print(f"Created portfolio: {spec['title']}")

        resume_service = ResumeService(
            resume_repo=SQLAlchemyResumeRepository(session),
            embedding_repo=SQLAlchemyEmbeddingRepository(session),
            embedding_provider=embedding_provider,
        )
        existing_resume_titles = {
            r.title
            for r in (await SQLAlchemyResumeRepository(session).list_all_for_user(user.id))
        }
        for spec in DEMO_RESUMES:
            if spec["title"] in existing_resume_titles:
                print(f"Resume already exists: {spec['title']}")
                continue
            await resume_service.create(user.id, ResumeCreate(**spec))
            print(f"Created resume: {spec['title']}")

        # ------------------------------------------------------------------
        # Phase 6: build a demo application end-to-end (analyze → match →
        # recommend → propose → apply). Idempotent: re-running does nothing
        # once an application exists.
        # ------------------------------------------------------------------
        ai_provider = build_ai_provider(settings)
        job_repo = SQLAlchemyJobRepository(session)
        analysis_repo = SQLAlchemyJobAnalysisRepository(session)
        score_repo = SQLAlchemyOpportunityScoreRepository(session)
        portfolio_repo = SQLAlchemyPortfolioRepository(session)
        resume_repo_ = SQLAlchemyResumeRepository(session)
        embedding_repo = SQLAlchemyEmbeddingRepository(session)
        proposal_repo = SQLAlchemyProposalRepository(session)
        app_repo = SQLAlchemyApplicationRepository(session)
        history_repo = SQLAlchemyApplicationHistoryRepository(session)

        portfolio_service_ = PortfolioService(
            portfolio_repo=portfolio_repo,
            embedding_repo=embedding_repo,
            embedding_provider=embedding_provider,
        )
        resume_service_ = ResumeService(
            resume_repo=resume_repo_,
            embedding_repo=embedding_repo,
            embedding_provider=embedding_provider,
        )
        matching_service = PortfolioMatchingService(
            job_repo=job_repo,
            portfolio_repo=portfolio_repo,
            analysis_repo=analysis_repo,
            embedding_repo=embedding_repo,
            portfolio_service=portfolio_service_,
            embedding_provider=embedding_provider,
            profile=DEFAULT_FREELANCER_PROFILE,
        )
        rec_service = ResumeRecommendationService(
            job_repo=job_repo,
            resume_repo=resume_repo_,
            analysis_repo=analysis_repo,
            embedding_repo=embedding_repo,
            resume_service=resume_service_,
            embedding_provider=embedding_provider,
        )

        demo_job = await jobs.get_by_source_hash(source_hash, user_id=user.id)
        if demo_job is not None:
            existing_app = await app_repo.find_active_for_job(
                user_id=user.id, job_id=demo_job.id
            )
            if existing_app is not None:
                print(f"Demo application already exists ({existing_app.status})")
            else:
                # 1. Analyze + score (idempotent)
                if await analysis_repo.get_by_job_id(demo_job.id) is None:
                    await JobAnalysisService(
                        job_repo=job_repo,
                        analysis_repo=analysis_repo,
                        score_repo=score_repo,
                        ai_provider=ai_provider,
                        scoring=ScoringService(DEFAULT_FREELANCER_PROFILE),
                    ).analyze(user_id=user.id, job_id=demo_job.id)
                    print("Analyzed demo job")
                # 2. Generate a proposal (idempotent: skip if one already exists)
                latest = await proposal_repo.get_latest_by_job_id(
                    demo_job.id, user_id=user.id
                )
                if latest is None:
                    gen = ProposalGenerationService(
                        job_repo=job_repo,
                        analysis_repo=analysis_repo,
                        score_repo=score_repo,
                        portfolio_repo=portfolio_repo,
                        portfolio_matching_service=matching_service,
                        resume_recommendation_service=rec_service,
                        proposal_repo=proposal_repo,
                        ai_provider=ai_provider,
                        review_service=ProposalReviewService(),
                    )
                    latest = await gen.generate(
                        user_id=user.id, job_id=demo_job.id
                    )
                    print(
                        f"Generated demo proposal "
                        f"(quality {latest.quality_score}/100)"
                    )
                # 3. Create application from proposal
                app_service = ApplicationService(
                    application_repo=app_repo,
                    history_repo=history_repo,
                    job_repo=job_repo,
                    proposal_repo=proposal_repo,
                    resume_repo=resume_repo_,
                    portfolio_repo=portfolio_repo,
                    score_repo=score_repo,
                    portfolio_matching_service=matching_service,
                    resume_recommendation_service=rec_service,
                )
                try:
                    proposal_id = (
                        latest.id if hasattr(latest, "id") else latest.id  # type: ignore[union-attr]
                    )
                    application = await app_service.create_from_proposal(
                        user_id=user.id,
                        proposal_id=proposal_id,
                        payload=CreateFromProposalRequest(
                            status="applied",
                            note="Seeded by scripts/seed.py.",
                        ),
                    )
                    print(
                        f"Created demo application {application.id} "
                        f"(status={application.status})"
                    )
                except AlreadyExistsError as exc:
                    print(f"Skipping demo application: {exc}")

        # ------------------------------------------------------------------
        # Phase 7: seed a varied set of applications so the analytics
        # dashboard has something to chew on. Idempotent: re-running won't
        # duplicate (we key off the job title).
        # ------------------------------------------------------------------
        analytics_specs = _ANALYTICS_DEMO_SPECS
        existing_titles = {
            j.title
            for j, _ in [
                (await jobs.get_by_source_hash(_hash_demo_text(spec["description"]), user_id=user.id), spec)
                for spec in analytics_specs
            ]
            if j is not None
        }

        analyzer_service = JobAnalysisService(
            job_repo=job_repo,
            analysis_repo=analysis_repo,
            score_repo=score_repo,
            ai_provider=ai_provider,
            scoring=ScoringService(DEFAULT_FREELANCER_PROFILE),
        )
        generator_service = ProposalGenerationService(
            job_repo=job_repo,
            analysis_repo=analysis_repo,
            score_repo=score_repo,
            portfolio_repo=portfolio_repo,
            portfolio_matching_service=matching_service,
            resume_recommendation_service=rec_service,
            proposal_repo=proposal_repo,
            ai_provider=ai_provider,
            review_service=ProposalReviewService(),
        )
        app_service_full = ApplicationService(
            application_repo=app_repo,
            history_repo=history_repo,
            job_repo=job_repo,
            proposal_repo=proposal_repo,
            resume_repo=resume_repo_,
            portfolio_repo=portfolio_repo,
            score_repo=score_repo,
            portfolio_matching_service=matching_service,
            resume_recommendation_service=rec_service,
        )

        for spec in analytics_specs:
            if spec["title"] in existing_titles:
                print(f"Analytics demo already exists: {spec['title']}")
                continue
            await _seed_analytics_application(
                session=session,
                user_id=user.id,
                spec=spec,
                jobs_repo=jobs,
                analyzer=analyzer_service,
                generator=generator_service,
                app_service=app_service_full,
            )

        print(
            f"\nEmbedding provider: {embedding_provider.name} "
            f"({embedding_provider.model_id})"
        )


if __name__ == "__main__":
    asyncio.run(main())
