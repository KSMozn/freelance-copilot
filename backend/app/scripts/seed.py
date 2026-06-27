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
from decimal import Decimal
from typing import Any

from app.application.dto.portfolio_dto import PortfolioCreate
from app.application.services.portfolio_service import PortfolioService
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
from app.infrastructure.db.repositories.sqlalchemy_portfolio_repository import (
    SQLAlchemyPortfolioRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)

DEMO_EMAIL = "demo@upwork-intel.local"
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

        print(
            f"\nEmbedding provider: {embedding_provider.name} "
            f"({embedding_provider.model_id})"
        )


if __name__ == "__main__":
    asyncio.run(main())
