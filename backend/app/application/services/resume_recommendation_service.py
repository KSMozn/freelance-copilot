"""Hybrid resume→job recommendation.

Score = 0.55·semantic + 0.30·skill_overlap + 0.10·domain_overlap + 0.05·seniority

Skill overlap is asymmetric and weighted: a primary_skills hit contributes
1.0, a secondary_skills hit contributes 0.5, of the total available signal.
Missing-or-weak skills are job-required skills the resume cannot demonstrate.

`suggested_positioning` is template-driven (Phase 6 will replace it with LLM
output) but always grounded in matched + missing skills + resume metadata.
"""
from __future__ import annotations

from uuid import UUID

from app.application.dto.resume_dto import (
    ResumeRecommendation,
    ResumeRecommendationsResponse,
)
from app.application.services.resume_service import RESUME_OWNER_TYPE, ResumeService
from app.domain.entities.analysis import JobAnalysis as DomainAnalysis
from app.domain.entities.job import Job
from app.domain.entities.resume import Resume
from app.domain.exceptions import NotFoundError
from app.domain.providers.embedding_provider import EmbeddingProvider
from app.domain.repositories.analysis_repository import JobAnalysisRepository
from app.domain.repositories.embedding_repository import EmbeddingRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.resume_repository import ResumeRepository

JOB_OWNER_TYPE = "job"

WEIGHT_SEMANTIC = 0.55
WEIGHT_SKILL = 0.30
WEIGHT_DOMAIN = 0.10
WEIGHT_SENIORITY = 0.05

DEFAULT_TOP_N = 3

_SENIORITY_ORDER = ("junior", "mid", "senior", "lead", "staff", "principal")
_SENIORITY_INDEX = {s: i for i, s in enumerate(_SENIORITY_ORDER)}


def _normalize(value: str) -> str:
    return value.strip().lower()


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
    if analysis.seniority:
        parts.append("Seniority: " + analysis.seniority)
    return "\n".join(parts)


def _skill_overlap(
    *,
    primary: list[str],
    secondary: list[str],
    job_skills: list[str],
) -> tuple[float, list[str], list[str]]:
    """Weighted asymmetric coverage of the job's required skills.

    Returns (score, relevant_skill_names, missing_skill_names).
    A primary hit is worth 1.0 of the per-job-skill point; a secondary hit
    is worth 0.5.
    """
    if not job_skills:
        return 0.0, [], []
    primary_norm = {_normalize(s): s for s in primary if s}
    secondary_norm = {_normalize(s): s for s in secondary if s}

    matched_names: list[str] = []
    missing: list[str] = []
    earned = 0.0
    available = 0.0
    seen_norm: set[str] = set()
    for js in job_skills:
        n = _normalize(js)
        if not n or n in seen_norm:
            continue
        seen_norm.add(n)
        available += 1.0
        if n in primary_norm:
            earned += 1.0
            matched_names.append(primary_norm[n])
        elif n in secondary_norm:
            earned += 0.5
            matched_names.append(secondary_norm[n])
        else:
            missing.append(js)
    if available == 0.0:
        return 0.0, [], []
    return earned / available, matched_names, missing


def _domain_overlap(resume_domains: list[str], job_domain: str | None) -> tuple[float, list[str]]:
    """Exact-or-substring match across the resume's listed domains."""
    if not job_domain or not resume_domains:
        return 0.0, []
    j = _normalize(job_domain)
    matches: list[str] = []
    best = 0.0
    for rd in resume_domains:
        n = _normalize(rd)
        if n == j:
            matches.append(rd)
            best = max(best, 1.0)
        elif n in j or j in n:
            matches.append(rd)
            best = max(best, 0.5)
    return best, matches


def _seniority_alignment(resume_level: str | None, job_level: str | None) -> float:
    if not resume_level or not job_level:
        return 0.5
    r = _SENIORITY_INDEX.get(_normalize(resume_level))
    j = _SENIORITY_INDEX.get(_normalize(job_level))
    if r is None or j is None:
        return 0.5
    delta = abs(r - j)
    if delta == 0:
        return 1.0
    if delta == 1:
        return 0.6
    if delta == 2:
        return 0.3
    return 0.1


def _fit_reasons(
    *,
    semantic: float,
    skill_score: float,
    matched_skills: list[str],
    domain_score: float,
    matched_domains: list[str],
    job_domain: str | None,
    seniority_score: float,
    resume_seniority: str | None,
    job_seniority: str | None,
) -> list[str]:
    reasons: list[str] = []
    if matched_skills:
        reasons.append(
            "Strong match with " + ", ".join(matched_skills[:6])
        )
    elif skill_score > 0:
        reasons.append("Partial coverage of the required skill set")
    if semantic >= 0.65:
        reasons.append("Resume positioning aligns closely with the job's framing")
    elif semantic >= 0.45:
        reasons.append("Moderate overall positioning fit with the job")
    if domain_score >= 1.0:
        reasons.append(
            f"Direct domain match ({matched_domains[0]})" if matched_domains else "Direct domain match"
        )
    elif domain_score > 0:
        reasons.append(
            f"Adjacent domain ({matched_domains[0]} ↔ {job_domain})"
            if matched_domains and job_domain
            else "Adjacent domain"
        )
    if seniority_score >= 1.0 and resume_seniority and job_seniority:
        reasons.append(f"Same seniority band ({resume_seniority})")
    elif seniority_score < 0.5 and resume_seniority and job_seniority:
        reasons.append(
            f"Seniority mismatch — resume is {resume_seniority}, job asks for {job_seniority}"
        )
    return reasons


def _positioning_suggestions(
    *,
    resume: Resume,
    matched_skills: list[str],
    missing_skills: list[str],
    job_seniority: str | None,
) -> list[str]:
    """Cheap, grounded suggestions. Phase 6 will swap these for LLM output."""
    suggestions: list[str] = []
    if matched_skills:
        head = ", ".join(matched_skills[:3])
        suggestions.append(f"Lead with recent {head} experience.")
    if resume.target_role:
        suggestions.append(
            f"Frame the application around your {resume.target_role} positioning."
        )
    if resume.project_highlights:
        suggestions.append(
            f"Mention the highlight: \"{resume.project_highlights[0]}\"."
        )
    if missing_skills:
        suggestions.append(
            "Acknowledge gap on "
            + ", ".join(missing_skills[:3])
            + " — note adjacent experience or willingness to ramp."
        )
    if job_seniority and resume.seniority_level and job_seniority != resume.seniority_level:
        suggestions.append(
            f"Calibrate tone — resume reads as {resume.seniority_level}; job is {job_seniority}."
        )
    # Resume titles like "Engineering Manager Resume" + a non-management job
    # need a soft warning. Heuristic, not exhaustive.
    title_l = resume.title.lower()
    if "manager" in title_l or "leadership" in title_l:
        suggestions.append(
            "Avoid over-emphasizing people management unless the job asks for it."
        )
    return suggestions[:5]


class ResumeRecommendationService:
    def __init__(
        self,
        *,
        job_repo: JobRepository,
        resume_repo: ResumeRepository,
        analysis_repo: JobAnalysisRepository,
        embedding_repo: EmbeddingRepository,
        resume_service: ResumeService,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._jobs = job_repo
        self._resumes = resume_repo
        self._analyses = analysis_repo
        self._embeddings = embedding_repo
        self._resume_svc = resume_service
        self._provider = embedding_provider

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

    async def recommend(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
        top_n: int = DEFAULT_TOP_N,
    ) -> ResumeRecommendationsResponse:
        job, analysis = await self._load_job_and_analysis(
            user_id=user_id, job_id=job_id
        )
        resumes = await self._resumes.list_all_for_user(user_id)

        if not resumes:
            return ResumeRecommendationsResponse(
                job_id=job.id,
                recommendations=[],
                embedding_provider=self._provider.name,
                embedding_model=self._provider.model,
                resume_count=0,
            )

        job_vec = await self._ensure_job_embedding(job=job, analysis=analysis)

        resume_vectors = await self._embeddings.get_many(
            owner_type=RESUME_OWNER_TYPE,
            owner_ids=[r.id for r in resumes],
            model=self._provider.model_id,
        )
        for r in resumes:
            if r.id not in resume_vectors:
                resume_vectors[r.id] = await self._resume_svc.ensure_embedding(r)

        job_skills = analysis.required_skills + analysis.preferred_skills + analysis.technologies
        job_domain = analysis.business_domain
        job_seniority = analysis.seniority

        recs: list[ResumeRecommendation] = []
        for resume in resumes:
            semantic = _semantic_score(job_vec, resume_vectors[resume.id])
            skill_score, matched_skills, missing_skills = _skill_overlap(
                primary=resume.primary_skills,
                secondary=resume.secondary_skills,
                job_skills=job_skills,
            )
            domain_score, matched_domains = _domain_overlap(resume.domains, job_domain)
            seniority_score = _seniority_alignment(resume.seniority_level, job_seniority)

            total = (
                WEIGHT_SEMANTIC * semantic
                + WEIGHT_SKILL * skill_score
                + WEIGHT_DOMAIN * domain_score
                + WEIGHT_SENIORITY * seniority_score
            )
            total = max(0.0, min(1.0, total))

            recs.append(
                ResumeRecommendation(
                    resume_id=resume.id,
                    title=resume.title,
                    match_score=round(total, 4),
                    semantic_score=round(semantic, 4),
                    skill_overlap_score=round(skill_score, 4),
                    domain_overlap_score=round(domain_score, 4),
                    seniority_alignment_score=round(seniority_score, 4),
                    fit_reasons=_fit_reasons(
                        semantic=semantic,
                        skill_score=skill_score,
                        matched_skills=matched_skills,
                        domain_score=domain_score,
                        matched_domains=matched_domains,
                        job_domain=job_domain,
                        seniority_score=seniority_score,
                        resume_seniority=resume.seniority_level,
                        job_seniority=job_seniority,
                    ),
                    relevant_skills=matched_skills,
                    missing_or_weak_skills=missing_skills[:5],
                    suggested_positioning=_positioning_suggestions(
                        resume=resume,
                        matched_skills=matched_skills,
                        missing_skills=missing_skills,
                        job_seniority=job_seniority,
                    ),
                )
            )

        recs.sort(key=lambda r: r.match_score, reverse=True)
        return ResumeRecommendationsResponse(
            job_id=job.id,
            recommendations=recs[:top_n],
            embedding_provider=self._provider.name,
            embedding_model=self._provider.model,
            resume_count=len(resumes),
        )


def hybrid_score(*, semantic: float, skill: float, domain: float, seniority: float) -> float:
    return (
        WEIGHT_SEMANTIC * semantic
        + WEIGHT_SKILL * skill
        + WEIGHT_DOMAIN * domain
        + WEIGHT_SENIORITY * seniority
    )
