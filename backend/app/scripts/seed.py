"""Insert a demo user + a realistic demo job ready for the AI analyzer.

Idempotent: re-running does nothing once the rows exist.

Run inside the backend container:

    docker compose exec backend python -m app.scripts.seed
"""
from __future__ import annotations

import asyncio
from decimal import Decimal

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.domain.entities.job import BudgetType, JobStatus
from app.infrastructure.db.repositories.sqlalchemy_job_repository import (
    SQLAlchemyJobRepository,
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


async def main() -> None:
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
        import hashlib
        import re

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


if __name__ == "__main__":
    asyncio.run(main())
