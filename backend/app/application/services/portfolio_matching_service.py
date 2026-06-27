"""Hybrid portfolio→job matching.

Score = 0.60·semantic + 0.25·skill_overlap + 0.10·domain_overlap + 0.05·strategic

All components live in [0, 1] so the total does too. Per-portfolio explanation
fields (match_reasons, talking points) are derived from which components fired
hardest — they're heuristic but always grounded in the underlying signal.

The service never calls back into pgvector ANN; portfolio sets per user are
small (tens, not millions). When that changes we can switch to an ivfflat ANN
query without touching the scoring rules.
"""
from __future__ import annotations

import math
from uuid import UUID

from app.application.dto.portfolio_dto import PortfolioMatch, PortfolioMatchesResponse
from app.application.services.portfolio_service import (
    PORTFOLIO_OWNER_TYPE,
    PortfolioService,
)
from app.domain.entities.analysis import JobAnalysis as DomainAnalysis
from app.domain.entities.job import Job
from app.domain.entities.portfolio import Portfolio
from app.domain.exceptions import NotFoundError
from app.domain.profiles.freelancer_profile import FreelancerProfile
from app.domain.providers.embedding_provider import EmbeddingProvider
from app.domain.repositories.analysis_repository import JobAnalysisRepository
from app.domain.repositories.embedding_repository import EmbeddingRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.portfolio_repository import PortfolioRepository

JOB_OWNER_TYPE = "job"

WEIGHT_SEMANTIC = 0.60
WEIGHT_SKILL = 0.25
WEIGHT_DOMAIN = 0.10
WEIGHT_STRATEGIC = 0.05

DEFAULT_TOP_N = 5


def _normalize_term(s: str) -> str:
    return s.strip().lower()


def _cosine_unit(a: list[float], b: list[float]) -> float:
    """Cosine for unit vectors → dot product. Robust to length mismatch (returns 0)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True))


def _semantic_score(a: list[float], b: list[float]) -> float:
    """Rescale cosine from [-1, 1] to [0, 1]."""
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
    portfolio_skills: list[str], job_skills: list[str]
) -> tuple[float, list[str]]:
    """Asymmetric: what fraction of the job's required skills the portfolio covers,
    plus the matching skill names (preserving portfolio casing for display).
    """
    if not job_skills:
        return 0.0, []
    job_norm = {_normalize_term(s) for s in job_skills if s}
    portfolio_norm = {_normalize_term(s): s for s in portfolio_skills if s}
    hits = [portfolio_norm[js] for js in job_norm if js in portfolio_norm]
    if not job_norm:
        return 0.0, []
    return len(hits) / len(job_norm), hits


def _domain_overlap(portfolio_domain: str | None, job_domain: str | None) -> float:
    if not portfolio_domain or not job_domain:
        return 0.0
    p = _normalize_term(portfolio_domain)
    j = _normalize_term(job_domain)
    if p == j:
        return 1.0
    # Substring match counts as half — domains like "Enterprise SaaS" partially
    # overlap with "AI SaaS" but are not the same.
    if p in j or j in p:
        return 0.5
    return 0.0


def _strategic_score(portfolio: Portfolio, profile: FreelancerProfile) -> float:
    haystack = " ".join(
        [
            portfolio.title,
            portfolio.short_description or "",
            portfolio.long_description,
            portfolio.business_domain or "",
            " ".join(portfolio.technologies),
            " ".join(portfolio.skills),
            " ".join(portfolio.features),
            " ".join(portfolio.outcomes),
        ]
    ).lower()
    hits = sum(1 for p in profile.strategic_priorities if p.lower() in haystack)
    if hits == 0:
        return 0.0
    return min(1.0, hits / 3.0)


def _match_reasons(
    *,
    semantic: float,
    skill_score: float,
    matched_skills: list[str],
    domain_overlap: float,
    portfolio_domain: str | None,
    job_domain: str | None,
    strategic: float,
) -> list[str]:
    reasons: list[str] = []
    if semantic >= 0.6:
        reasons.append("Strong overall semantic similarity to the job description")
    elif semantic >= 0.4:
        reasons.append("Moderate semantic overlap with the job description")
    if matched_skills:
        reasons.append(
            "Direct skill overlap: " + ", ".join(matched_skills[:6])
        )
    elif skill_score > 0:
        reasons.append("Some skill overlap with the job's required stack")
    if domain_overlap >= 1.0:
        reasons.append(
            f"Same business domain ({portfolio_domain})" if portfolio_domain else "Same domain"
        )
    elif domain_overlap > 0:
        reasons.append(
            f"Adjacent domain — yours: {portfolio_domain}, job: {job_domain}"
        )
    if strategic > 0.4:
        reasons.append("Hits multiple of your strategic priorities")
    return reasons


def _talking_points(
    *,
    matched_skills: list[str],
    portfolio: Portfolio,
) -> list[str]:
    """Cheap template-driven suggestions. The proposal-generation phase will
    replace these with LLM-authored bullets, but for Phase 3 these get the
    user 80% of the value without any model call.
    """
    points: list[str] = []
    if matched_skills:
        head = matched_skills[0]
        points.append(
            f"Lead with the {portfolio.title} project — it used {head} in a "
            f"production setting."
        )
    if portfolio.outcomes:
        points.append(
            f"Quote a concrete outcome: \"{portfolio.outcomes[0]}\"."
        )
    elif portfolio.features:
        points.append(
            f"Highlight the feature \"{portfolio.features[0]}\" as evidence."
        )
    if portfolio.business_domain:
        points.append(
            f"Frame your experience in the {portfolio.business_domain} domain "
            "to match the client's vertical."
        )
    if portfolio.github_url:
        points.append(f"Offer to share the source / write-up at {portfolio.github_url}.")
    return points[:4]


def _relevant_domains(portfolio: Portfolio, job_domain: str | None) -> list[str]:
    domains: list[str] = []
    if portfolio.business_domain:
        domains.append(portfolio.business_domain)
    if job_domain and job_domain not in domains:
        domains.append(job_domain)
    return domains


class PortfolioMatchingService:
    def __init__(
        self,
        *,
        job_repo: JobRepository,
        portfolio_repo: PortfolioRepository,
        analysis_repo: JobAnalysisRepository,
        embedding_repo: EmbeddingRepository,
        portfolio_service: PortfolioService,
        embedding_provider: EmbeddingProvider,
        profile: FreelancerProfile,
    ) -> None:
        self._jobs = job_repo
        self._portfolios = portfolio_repo
        self._analyses = analysis_repo
        self._embeddings = embedding_repo
        self._portfolio_svc = portfolio_service
        self._provider = embedding_provider
        self._profile = profile

    async def _load_job_and_analysis(
        self, *, user_id: UUID, job_id: UUID
    ) -> tuple[Job, DomainAnalysis]:
        job = await self._jobs.get_by_id(job_id, user_id=user_id)
        if job is None:
            raise NotFoundError("Job not found")
        analysis = await self._analyses.get_by_job_id(job_id)
        if analysis is None:
            raise NotFoundError(
                "Job has not been analyzed yet — run /analyze first."
            )
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
    ) -> PortfolioMatchesResponse:
        job, analysis = await self._load_job_and_analysis(
            user_id=user_id, job_id=job_id
        )
        portfolios = await self._portfolios.list_all_for_user(user_id)

        if not portfolios:
            return PortfolioMatchesResponse(
                job_id=job.id,
                matches=[],
                embedding_provider=self._provider.name,
                embedding_model=self._provider.model,
                portfolio_count=0,
            )

        job_vec = await self._ensure_job_embedding(job=job, analysis=analysis)

        # Try to fetch portfolio embeddings in one shot; lazily embed the misses
        portfolio_vectors = await self._embeddings.get_many(
            owner_type=PORTFOLIO_OWNER_TYPE,
            owner_ids=[p.id for p in portfolios],
            model=self._provider.model_id,
        )
        for p in portfolios:
            if p.id not in portfolio_vectors:
                portfolio_vectors[p.id] = await self._portfolio_svc.ensure_embedding(p)

        job_required_skills = (
            analysis.required_skills + analysis.preferred_skills + analysis.technologies
        )
        job_domain = analysis.business_domain

        matches: list[PortfolioMatch] = []
        for portfolio in portfolios:
            semantic = _semantic_score(job_vec, portfolio_vectors[portfolio.id])
            skill_score, matched_skills = _skill_overlap(
                portfolio.skills + portfolio.technologies, job_required_skills
            )
            domain_overlap = _domain_overlap(portfolio.business_domain, job_domain)
            strategic = _strategic_score(portfolio, self._profile)

            total = (
                WEIGHT_SEMANTIC * semantic
                + WEIGHT_SKILL * skill_score
                + WEIGHT_DOMAIN * domain_overlap
                + WEIGHT_STRATEGIC * strategic
            )
            total = max(0.0, min(1.0, total))

            matches.append(
                PortfolioMatch(
                    portfolio_id=portfolio.id,
                    title=portfolio.title,
                    match_score=round(total, 4),
                    semantic_score=round(semantic, 4),
                    skill_overlap_score=round(skill_score, 4),
                    domain_overlap_score=round(domain_overlap, 4),
                    strategic_score=round(strategic, 4),
                    match_reasons=_match_reasons(
                        semantic=semantic,
                        skill_score=skill_score,
                        matched_skills=matched_skills,
                        domain_overlap=domain_overlap,
                        portfolio_domain=portfolio.business_domain,
                        job_domain=job_domain,
                        strategic=strategic,
                    ),
                    relevant_skills=matched_skills,
                    relevant_domains=_relevant_domains(portfolio, job_domain),
                    suggested_talking_points=_talking_points(
                        matched_skills=matched_skills, portfolio=portfolio
                    ),
                )
            )

        matches.sort(key=lambda m: m.match_score, reverse=True)

        return PortfolioMatchesResponse(
            job_id=job.id,
            matches=matches[:top_n],
            embedding_provider=self._provider.name,
            embedding_model=self._provider.model,
            portfolio_count=len(portfolios),
        )


# Re-export for testing: a tiny helper used in unit tests + the smoke script.
def cosine_for_unit_vectors(a: list[float], b: list[float]) -> float:
    return _cosine_unit(a, b)


def hybrid_score(*, semantic: float, skill: float, domain: float, strategic: float) -> float:
    return (
        WEIGHT_SEMANTIC * semantic
        + WEIGHT_SKILL * skill
        + WEIGHT_DOMAIN * domain
        + WEIGHT_STRATEGIC * strategic
    )


def euclidean_distance(a: list[float], b: list[float]) -> float:
    """Available for diagnostics; not used in scoring."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b, strict=True)))
