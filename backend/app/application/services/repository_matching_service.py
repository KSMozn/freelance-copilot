"""Hybrid Repository→Job matching.

Score = 0.55·semantic + 0.30·skill_overlap + 0.10·domain_overlap + 0.05·architecture

Where `architecture` rewards repos that have evidence of production-grade
practices (Docker / CI / tests) — a cheap proxy for "this is a real, shipped
codebase" rather than a tutorial fork. Distinct from PortfolioMatching's
`strategic_score` because scanned repos don't carry curated strategic
priorities.
"""
from __future__ import annotations

import re
from uuid import UUID

from app.application.dto.repository_dto import (
    RepositoryMatch,
    RepositoryMatchesResponse,
)
from app.application.services.repository_service import (
    REPOSITORY_OWNER_TYPE,
    RepositoryService,
)
from app.domain.entities.analysis import JobAnalysis as DomainAnalysis
from app.domain.entities.job import Job
from app.domain.entities.repository import Repository
from app.domain.exceptions import NotFoundError
from app.domain.providers.embedding_provider import EmbeddingProvider
from app.domain.repositories.analysis_repository import JobAnalysisRepository
from app.domain.repositories.embedding_repository import EmbeddingRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.repository_store import RepositoryStore

JOB_OWNER_TYPE = "job"

WEIGHT_SEMANTIC = 0.55
WEIGHT_SKILL = 0.30
WEIGHT_DOMAIN = 0.10
WEIGHT_ARCHITECTURE = 0.05

DEFAULT_TOP_N = 5


def _normalize(s: str) -> str:
    return s.strip().lower()


def _cosine_unit(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True))


def _semantic_score(a: list[float], b: list[float]) -> float:
    cos = _cosine_unit(a, b)
    return max(0.0, min(1.0, (cos + 1.0) / 2.0))


def _build_job_text(*, job: Job, analysis: DomainAnalysis) -> str:
    parts: list[str] = [job.title]
    if analysis.summary:
        parts.append(analysis.summary)
    parts.append(job.description)
    if analysis.required_skills:
        parts.append("Required skills: " + ", ".join(analysis.required_skills))
    if analysis.preferred_skills:
        parts.append("Preferred skills: " + ", ".join(analysis.preferred_skills))
    if analysis.technologies:
        parts.append("Technologies: " + ", ".join(analysis.technologies))
    if analysis.business_domain:
        parts.append("Domain: " + analysis.business_domain)
    if analysis.expected_deliverables:
        parts.append("Deliverables: " + " · ".join(analysis.expected_deliverables))
    return "\n".join(parts)


def _skill_overlap(
    repo_skills: list[str], job_skills: list[str]
) -> tuple[float, list[str], list[str]]:
    """Asymmetric: fraction of job's required skills the repo covers.

    Returns (score, matched_in_repo_casing, missing_in_job_casing).
    """
    if not job_skills:
        return 0.0, [], []
    job_norm = {_normalize(s): s for s in job_skills if s}
    repo_norm = {_normalize(s): s for s in repo_skills if s}
    matched_keys = [k for k in job_norm if k in repo_norm]
    missing_keys = [k for k in job_norm if k not in repo_norm]
    score = len(matched_keys) / len(job_norm) if job_norm else 0.0
    matched = [repo_norm[k] for k in matched_keys]
    missing = [job_norm[k] for k in missing_keys]
    return score, matched, missing


def _domain_overlap(repo_domain: str | None, job_domain: str | None) -> float:
    if not repo_domain or not job_domain:
        return 0.0
    r = _normalize(repo_domain)
    j = _normalize(job_domain)
    if r == j:
        return 1.0
    if r in j or j in r:
        return 0.5
    return 0.0


def _architecture_score(repo: Repository) -> float:
    """0–1 score based on production-grade signals."""
    points = 0.0
    if repo.has_docker:
        points += 0.4
    if repo.has_ci:
        points += 0.3
    if repo.has_tests:
        points += 0.2
    if repo.architecture_summary:
        points += 0.1
    return min(1.0, points)


def _match_reasons(
    *,
    semantic: float,
    matched_skills: list[str],
    domain_overlap: float,
    repo_domain: str | None,
    job_domain: str | None,
    repo: Repository,
) -> list[str]:
    reasons: list[str] = []
    if semantic >= 0.6:
        reasons.append("Strong semantic match to the job description")
    elif semantic >= 0.4:
        reasons.append("Moderate semantic overlap with the job description")
    if matched_skills:
        reasons.append("Stack overlap: " + ", ".join(matched_skills[:6]))
    if domain_overlap >= 1.0 and repo_domain:
        reasons.append(f"Same business domain ({repo_domain})")
    elif domain_overlap > 0:
        reasons.append(f"Adjacent domain — repo: {repo_domain}, job: {job_domain}")
    if repo.has_docker and repo.has_ci:
        reasons.append("Production-grade: Docker + CI evidence in the repo")
    elif repo.has_tests:
        reasons.append("Has automated tests")
    return reasons


def _talking_points(*, matched_skills: list[str], repo: Repository) -> list[str]:
    points: list[str] = []
    if matched_skills:
        head = matched_skills[0]
        points.append(
            f"Lead with {repo.owner}/{repo.name} — concrete {head} evidence in the codebase."
        )
    if repo.architecture_summary:
        points.append(
            f"Quote the architecture: \"{repo.architecture_summary[:160].strip()}\""
        )
    if repo.highlights:
        points.append(f"Highlight: \"{repo.highlights[0]}\"")
    points.append(f"Offer to share the repo: {repo.github_url}")
    return points[:4]


def _relevant_paths(repo: Repository, skills: list[str], *, limit: int = 8) -> list[str]:
    """Pick file paths from the repo's stored index that contain any of the
    matched-skill keywords. Cheap substring scan — good enough to surface
    "here's the file that proves it" links in the proposal.
    """
    if not repo.path_index or not skills:
        return []
    needles: list[str] = []
    for skill in skills:
        bare = _normalize(skill)
        if not bare:
            continue
        # Split multi-word skills like "Authentication / JWT" into tokens.
        for token in re.split(r"[\s/+_\-]+", bare):
            token = token.strip()
            if len(token) >= 3 and token not in needles:
                needles.append(token)
    if not needles:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for path in repo.path_index:
        path_lc = path.lower()
        if any(n in path_lc for n in needles) and path not in seen:
            seen.add(path)
            out.append(path)
            if len(out) >= limit:
                break
    return out


def _relevant_domains(repo: Repository, job_domain: str | None) -> list[str]:
    domains: list[str] = []
    if repo.business_domain:
        domains.append(repo.business_domain)
    if job_domain and job_domain not in domains:
        domains.append(job_domain)
    return domains


class RepositoryMatchingService:
    def __init__(
        self,
        *,
        job_repo: JobRepository,
        repository_store: RepositoryStore,
        analysis_repo: JobAnalysisRepository,
        embedding_repo: EmbeddingRepository,
        repository_service: RepositoryService,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._jobs = job_repo
        self._store = repository_store
        self._analyses = analysis_repo
        self._embeddings = embedding_repo
        self._repo_svc = repository_service
        self._provider = embedding_provider

    async def _load_job_and_analysis(
        self, *, user_id: UUID, job_id: UUID
    ) -> tuple[Job, DomainAnalysis]:
        job = await self._jobs.get_by_id(job_id, user_id=user_id)
        if job is None:
            raise NotFoundError("Job not found")
        analysis = await self._analyses.get_by_job_id(job_id)
        if analysis is None:
            raise NotFoundError("Job has not been analyzed yet — run /analyze first.")
        return job, analysis

    async def _ensure_job_embedding(
        self, *, job: Job, analysis: DomainAnalysis
    ) -> list[float]:
        existing = await self._embeddings.get(
            owner_type=JOB_OWNER_TYPE,
            owner_id=job.id,
            model=self._provider.model_id,
        )
        if existing is not None:
            return existing
        text = _build_job_text(job=job, analysis=analysis)
        vec = await self._provider.embed(text)
        await self._embeddings.upsert(
            owner_type=JOB_OWNER_TYPE,
            owner_id=job.id,
            model=self._provider.model_id,
            vector=vec,
        )
        return vec

    async def match(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
        top_n: int = DEFAULT_TOP_N,
    ) -> RepositoryMatchesResponse:
        job, analysis = await self._load_job_and_analysis(
            user_id=user_id, job_id=job_id
        )
        repos = [
            r for r in await self._store.list_all_for_user(user_id)
            if r.scan_status == "scanned"
        ]
        if not repos:
            return RepositoryMatchesResponse(
                job_id=job.id,
                matches=[],
                embedding_provider=self._provider.name,
                embedding_model=self._provider.model,
                repository_count=0,
            )

        job_vec = await self._ensure_job_embedding(job=job, analysis=analysis)
        repo_vectors = await self._embeddings.get_many(
            owner_type=REPOSITORY_OWNER_TYPE,
            owner_ids=[r.id for r in repos],
            model=self._provider.model_id,
        )
        for r in repos:
            if r.id not in repo_vectors:
                repo_vectors[r.id] = await self._repo_svc.ensure_embedding(r)

        required_skills = (
            analysis.required_skills + analysis.preferred_skills + analysis.technologies
        )
        job_domain = analysis.business_domain

        matches: list[RepositoryMatch] = []
        for repo in repos:
            semantic = _semantic_score(job_vec, repo_vectors[repo.id])
            skill_score, matched, missing = _skill_overlap(
                repo.derived_skills(), required_skills
            )
            domain = _domain_overlap(repo.business_domain, job_domain)
            arch = _architecture_score(repo)

            total = (
                WEIGHT_SEMANTIC * semantic
                + WEIGHT_SKILL * skill_score
                + WEIGHT_DOMAIN * domain
                + WEIGHT_ARCHITECTURE * arch
            )
            total = max(0.0, min(1.0, total))

            matches.append(
                RepositoryMatch(
                    repository_id=repo.id,
                    owner=repo.owner,
                    name=repo.name,
                    github_url=repo.github_url,
                    match_score=round(total, 4),
                    semantic_score=round(semantic, 4),
                    skill_overlap_score=round(skill_score, 4),
                    domain_overlap_score=round(domain, 4),
                    architecture_score=round(arch, 4),
                    match_reasons=_match_reasons(
                        semantic=semantic,
                        matched_skills=matched,
                        domain_overlap=domain,
                        repo_domain=repo.business_domain,
                        job_domain=job_domain,
                        repo=repo,
                    ),
                    matched_skills=matched,
                    missing_skills=missing,
                    relevant_domains=_relevant_domains(repo, job_domain),
                    relevant_paths=_relevant_paths(repo, matched),
                    suggested_talking_points=_talking_points(
                        matched_skills=matched, repo=repo
                    ),
                )
            )

        matches.sort(key=lambda m: m.match_score, reverse=True)
        return RepositoryMatchesResponse(
            job_id=job.id,
            matches=matches[:top_n],
            embedding_provider=self._provider.name,
            embedding_model=self._provider.model,
            repository_count=len(repos),
        )
