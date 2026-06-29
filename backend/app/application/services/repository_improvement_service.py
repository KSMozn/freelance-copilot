"""Repo improvement suggestions: which gaps would lift future win rates.

Tallies skill frequency across the user's analyzed jobs (binary per-job
appearance), then for each scanned repository surfaces the most-requested
skills the repo doesn't yet cover. Each gap gets a short imperative
suggestion ("Implement Stripe Billing.").

Pure computation — no LLM call. The suggestion text is a small template
dictionary keyed by canonical skill name; unknown skills get a generic
fallback so the report stays informative even for niche stacks.
"""
from __future__ import annotations

from uuid import UUID

from app.application.dto.repository_improvement_dto import (
    RepositoryImprovement,
    RepositoryImprovements,
    RepositoryImprovementsReport,
)
from app.domain.entities.repository import Repository
from app.domain.repositories.analysis_repository import JobAnalysisRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.repository_store import RepositoryStore

# How many gaps to surface per repo. Spec sample shows ~8.
MAX_IMPROVEMENTS_PER_REPO = 8

# Hand-tuned imperatives for skills that show up frequently on Upwork.
# Unknown skills fall back to f"Add {skill} support." — keeps the report
# useful for niche stacks without forcing me to maintain an exhaustive list.
_SUGGESTION_TEMPLATES: dict[str, str] = {
    "stripe": "Implement Stripe Billing.",
    "openai": "Add an OpenAI provider integration.",
    "anthropic": "Add an Anthropic/Claude provider integration.",
    "claude": "Add an Anthropic/Claude provider integration.",
    "llm": "Add an LLM provider abstraction.",
    "rag": "Add a RAG pipeline over a document corpus.",
    "ai": "Add an LLM-backed AI feature.",
    "ml": "Add an ML inference path.",
    "tensorflow": "Add a TensorFlow inference path.",
    "pytorch": "Add a PyTorch inference path.",
    "next.js": "Migrate or add a Next.js front end.",
    "react": "Add a React front end.",
    "vue": "Add a Vue front end.",
    "tailwind": "Adopt Tailwind for the UI layer.",
    "node.js": "Add a Node.js service.",
    "typescript": "Convert the TypeScript layer / add type coverage.",
    "fastapi": "Add a FastAPI service.",
    "django": "Add a Django service.",
    "flask": "Add a Flask service.",
    "postgresql": "Add PostgreSQL persistence.",
    "mysql": "Add MySQL persistence.",
    "mongodb": "Add MongoDB persistence.",
    "redis": "Add Redis (caching / pub-sub / rate-limit).",
    "pgvector": "Add pgvector embeddings storage.",
    "docker": "Add Dockerfile + compose for local + prod parity.",
    "kubernetes": "Add Kubernetes manifests / Helm chart.",
    "aws": "Add an AWS deployment surface.",
    "gcp": "Add a GCP deployment surface.",
    "azure": "Add an Azure deployment surface.",
    "vercel": "Add a Vercel deployment path.",
    "graphql": "Expose a GraphQL API.",
    "rest": "Expose a REST API.",
    "grpc": "Expose a gRPC API.",
    "kafka": "Add a Kafka event stream.",
    "rabbitmq": "Add a RabbitMQ queue.",
    "jwt": "Add JWT-based authentication.",
    "oauth": "Add OAuth login.",
    "authentication / jwt": "Add JWT-based authentication.",
    "rbac": "Add role-based access control.",
    "role-based authentication": "Add role-based access control.",
    "admin dashboard": "Add an admin UI.",
    "audit logs": "Add an audit log trail.",
    "multi-tenancy": "Add tenant isolation (row-level or schema-per-tenant).",
    "usage analytics": "Add a usage / analytics dashboard.",
    "background jobs": "Add a background worker (BullMQ / Redis / Celery).",
    "webhook infrastructure": "Add a retryable webhook processor with idempotency.",
    "automated testing": "Add an automated test suite + CI runner.",
    "production deployment": "Set up a production deployment pipeline.",
}


def _suggestion_for(skill: str) -> str:
    canon = skill.strip().lower()
    if canon in _SUGGESTION_TEMPLATES:
        return _SUGGESTION_TEMPLATES[canon]
    return f"Add {skill} support."


def _job_skill_set(analysis) -> set[str]:
    """Lowercased set of every skill the analyzer flagged for one job.

    Combines `stack_requirements` (with category metadata) plus the legacy
    `required_skills` / `preferred_skills` / `technologies` lists so older
    analyses without `stack_requirements` still contribute to the tally.
    """
    skills: set[str] = set()
    for sr in analysis.stack_requirements:
        if sr.name:
            skills.add(sr.name.strip().lower())
    for s in analysis.required_skills + analysis.preferred_skills + analysis.technologies:
        if s:
            skills.add(s.strip().lower())
    return skills


def _repo_skill_set(repo: Repository) -> set[str]:
    """Lowercased set of every signal the scanner detected on a repo."""
    return {s.strip().lower() for s in repo.derived_skills() if s}


def _pick_display_name(skill_lc: str, sources: list[str]) -> str:
    """Pick the first non-lowercased display form we've seen for a skill."""
    for raw in sources:
        if raw and raw.strip().lower() == skill_lc:
            return raw.strip()
    return skill_lc


class RepositoryImprovementService:
    def __init__(
        self,
        *,
        job_repo: JobRepository,
        analysis_repo: JobAnalysisRepository,
        repository_store: RepositoryStore,
    ) -> None:
        self._jobs = job_repo
        self._analyses = analysis_repo
        self._repositories = repository_store

    async def build(self, *, user_id: UUID) -> RepositoryImprovementsReport:
        jobs_page = await self._jobs.list_for_user(
            user_id,
            status=None,
            limit=100,
            offset=0,
            search=None,
        )
        # list_for_user returns (items, total) where items is list[(Job, OpportunityScore|None)]
        jobs = [job for job, _score in jobs_page[0]]

        # Tally: for each skill key, count distinct jobs that ask for it and
        # remember the first nicely-cased display form for the UI.
        job_count = 0
        skill_to_count: dict[str, int] = {}
        skill_display_pool: dict[str, list[str]] = {}
        for job in jobs:
            analysis = await self._analyses.get_by_job_id(job.id)
            if analysis is None:
                continue
            job_count += 1
            job_skills = _job_skill_set(analysis)
            for skill_lc in job_skills:
                skill_to_count[skill_lc] = skill_to_count.get(skill_lc, 0) + 1
                if skill_lc not in skill_display_pool:
                    skill_display_pool[skill_lc] = []
                # Collect every source variant so we can recover good casing.
                skill_display_pool[skill_lc].extend(
                    sr.name for sr in analysis.stack_requirements if sr.name
                )
                skill_display_pool[skill_lc].extend(analysis.required_skills)
                skill_display_pool[skill_lc].extend(analysis.preferred_skills)
                skill_display_pool[skill_lc].extend(analysis.technologies)

        repos = await self._repositories.list_all_for_user(user_id)

        results: list[RepositoryImprovements] = []
        for repo in repos:
            repo_skills = _repo_skill_set(repo)
            gaps: list[tuple[str, int]] = [
                (skill_lc, count)
                for skill_lc, count in skill_to_count.items()
                if skill_lc not in repo_skills
            ]
            # Sort by frequency desc, then alphabetically for stability.
            gaps.sort(key=lambda kv: (-kv[1], kv[0]))

            improvements: list[RepositoryImprovement] = []
            for skill_lc, count in gaps[:MAX_IMPROVEMENTS_PER_REPO]:
                display = _pick_display_name(skill_lc, skill_display_pool.get(skill_lc, []))
                improvements.append(
                    RepositoryImprovement(
                        skill=display,
                        suggestion=_suggestion_for(display),
                        job_frequency=count,
                        job_frequency_pct=round(count / job_count, 4) if job_count else 0.0,
                    )
                )

            results.append(
                RepositoryImprovements(
                    repository_id=repo.id,
                    owner=repo.owner,
                    name=repo.name,
                    github_url=repo.github_url,
                    improvements=improvements,
                )
            )

        # Sort repos with the most-improvable first so the UI surfaces the
        # biggest opportunity at the top.
        results.sort(key=lambda r: -len(r.improvements))
        return RepositoryImprovementsReport(
            repositories=results,
            analyzed_job_count=job_count,
            repository_count=len(repos),
        )
