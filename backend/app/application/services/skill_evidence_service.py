"""Per-skill evidence + gap analysis.

For each skill the analyzer extracted (required, preferred, technologies, and
structured `stack_requirements`), this service walks the user's portfolios,
resume, and scanned repositories looking for concrete sentences that
demonstrate the skill. Output is a Strong / Weak / Missing rollup the UI
renders as a gap table.

Pure computation — no LLM call. Snippet selection is heuristic and prefers
outcome-flavored sentences over generic descriptions.
"""
from __future__ import annotations

import re
from uuid import UUID

from app.application.dto.evidence_dto import (
    EvidenceItem,
    EvidenceReport,
    SkillEvidence,
)
from app.domain.entities.analysis import JobAnalysis, StackRequirement
from app.domain.entities.portfolio import Portfolio
from app.domain.entities.repository import Repository
from app.domain.entities.resume import Resume
from app.domain.exceptions import NotFoundError
from app.domain.repositories.analysis_repository import JobAnalysisRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.portfolio_repository import PortfolioRepository
from app.domain.repositories.repository_store import RepositoryStore
from app.domain.repositories.resume_repository import ResumeRepository

# Confidence thresholds — the same rollup buckets the UI groups by.
STRONG_THRESHOLD = 0.7
WEAK_THRESHOLD = 0.4


def _norm(s: str) -> str:
    return s.strip().lower()


def _word_boundary_search(haystack: str, needle: str) -> bool:
    if not needle:
        return False
    # Match the skill as a token. Escape regex specials; allow `.NET`, `C++` to
    # surface even when they sit next to punctuation.
    pattern = rf"(?<![A-Za-z0-9]){re.escape(needle)}(?![A-Za-z0-9])"
    return re.search(pattern, haystack, flags=re.IGNORECASE) is not None


def _split_sentences(text: str) -> list[str]:
    """Cheap sentence splitter — good enough for short portfolio fields."""
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _pick_evidence_sentence(skill: str, text: str | None) -> str | None:
    if not text:
        return None
    for sentence in _split_sentences(text):
        if _word_boundary_search(sentence, skill):
            return sentence[:240]
    return None


def _portfolio_snippet(skill: str, p: Portfolio) -> str | None:
    """Pick the most concrete portfolio sentence that mentions `skill`.

    Preference order: outcomes (most concrete) > features > short_description
    > long_description.
    """
    for outcome in p.outcomes:
        if _word_boundary_search(outcome, skill):
            return outcome[:240]
    for feature in p.features:
        if _word_boundary_search(feature, skill):
            return feature[:240]
    snippet = _pick_evidence_sentence(skill, p.short_description)
    if snippet:
        return snippet
    snippet = _pick_evidence_sentence(skill, p.long_description)
    if snippet:
        return snippet
    # Last resort: the skill is listed but no narrative — still counts as
    # weaker evidence ("listed in tech stack").
    inventory = " ".join(p.technologies + p.skills)
    if _word_boundary_search(inventory, skill):
        return f"Listed in the {p.title} project stack."
    return None


def _resume_snippet(skill: str, r: Resume) -> str | None:
    for ach in r.achievements:
        if _word_boundary_search(ach, skill):
            return ach[:240]
    for hi in r.project_highlights:
        if _word_boundary_search(hi, skill):
            return hi[:240]
    snippet = _pick_evidence_sentence(skill, r.summary)
    if snippet:
        return snippet
    inventory = " ".join(r.primary_skills + r.secondary_skills + r.keywords)
    if _word_boundary_search(inventory, skill):
        return f"Listed under the {r.title} resume."
    return None


def _repo_snippet(skill: str, repo: Repository) -> str | None:
    for highlight in repo.highlights:
        if _word_boundary_search(highlight, skill):
            return highlight[:240]
    for strength in repo.strengths:
        if _word_boundary_search(strength, skill):
            return strength[:240]
    snippet = _pick_evidence_sentence(skill, repo.architecture_summary)
    if snippet:
        return snippet
    snippet = _pick_evidence_sentence(skill, repo.description)
    if snippet:
        return snippet
    if _word_boundary_search(" ".join(repo.derived_skills()), skill):
        return f"Detected in the {repo.owner}/{repo.name} codebase."
    return None


def _is_listing_sentence(snippet: str) -> bool:
    """Heuristic: 'Listed in …' / 'Detected in …' style sentences are weaker
    than concrete outcome statements; we use this to discount confidence.
    """
    head = snippet.lower()
    return head.startswith(("listed in", "listed under", "detected in"))


def _confidence(items: list[EvidenceItem]) -> float:
    """0.0 = nothing found. 0.4 = one weak listing. 1.0 = several concrete
    outcome-flavored sentences across multiple sources.
    """
    if not items:
        return 0.0
    sources_used = {i.source_type for i in items}
    concrete_hits = sum(1 for i in items if not _is_listing_sentence(i.snippet))
    listing_hits = len(items) - concrete_hits

    base = 0.35 * len(sources_used)  # one source = 0.35, three = 1.0 (capped)
    bonus = 0.15 * min(concrete_hits, 3) + 0.05 * min(listing_hits, 2)
    return max(0.0, min(1.0, base + bonus))


def _classify(confidence: float) -> str:
    if confidence >= STRONG_THRESHOLD:
        return "strong"
    if confidence >= WEAK_THRESHOLD:
        return "weak"
    return "missing" if confidence == 0 else "weak"


def _best_snippet(items: list[EvidenceItem]) -> str | None:
    """Prefer concrete (non-listing) snippets and shorter, more declarative ones."""
    if not items:
        return None
    concrete = [i for i in items if not _is_listing_sentence(i.snippet)]
    pool = concrete or items
    # Shortest concrete sentence reads as the punchiest evidence.
    pool.sort(key=lambda i: len(i.snippet))
    return pool[0].snippet


def _candidate_skills(
    analysis: JobAnalysis,
) -> list[tuple[str, StackRequirement | None]]:
    """Union of analyzer-extracted skills, keyed back to a `stack_requirements`
    entry when one exists (so we can pass `category` + `importance` to the UI).
    """
    stack_by_key: dict[str, StackRequirement] = {}
    for sr in analysis.stack_requirements:
        key = _norm(sr.name)
        # Keep the highest-importance entry for duplicates.
        prior = stack_by_key.get(key)
        if prior is None or sr.importance > prior.importance:
            stack_by_key[key] = sr

    keep: dict[str, tuple[str, StackRequirement | None]] = {}

    def _add(name: str) -> None:
        name = name.strip()
        if not name:
            return
        key = _norm(name)
        if key in keep:
            return
        keep[key] = (name, stack_by_key.get(key))

    # Iterate stack_requirements first so their display name + metadata wins.
    for sr in analysis.stack_requirements:
        _add(sr.name)
    for s in analysis.required_skills:
        _add(s)
    for s in analysis.preferred_skills:
        _add(s)
    for s in analysis.technologies:
        _add(s)

    return list(keep.values())


class SkillEvidenceService:
    def __init__(
        self,
        *,
        job_repo: JobRepository,
        analysis_repo: JobAnalysisRepository,
        portfolio_repo: PortfolioRepository,
        resume_repo: ResumeRepository,
        repository_store: RepositoryStore,
    ) -> None:
        self._jobs = job_repo
        self._analyses = analysis_repo
        self._portfolios = portfolio_repo
        self._resumes = resume_repo
        self._repositories = repository_store

    async def build(self, *, user_id: UUID, job_id: UUID) -> EvidenceReport:
        job = await self._jobs.get_by_id(job_id, user_id=user_id)
        if job is None:
            raise NotFoundError("Job not found")
        analysis = await self._analyses.get_by_job_id(job_id)
        if analysis is None:
            raise NotFoundError("Job has not been analyzed yet — run /analyze first.")

        portfolios = await self._portfolios.list_all_for_user(user_id)
        resumes_page = await self._resumes.list_for_user(
            user_id, search=None, domain=None, skill=None, limit=100, offset=0
        )
        resumes = resumes_page[0] if isinstance(resumes_page, tuple) else resumes_page
        repos = [
            r for r in await self._repositories.list_all_for_user(user_id)
            if r.scan_status == "scanned"
        ]

        candidates = _candidate_skills(analysis)
        skills: list[SkillEvidence] = []
        for skill_name, sr in candidates:
            items: list[EvidenceItem] = []

            for p in portfolios:
                snippet = _portfolio_snippet(skill_name, p)
                if snippet:
                    items.append(
                        EvidenceItem(
                            source_type="portfolio",
                            source_id=p.id,
                            source_label=p.title,
                            snippet=snippet,
                        )
                    )

            for r in resumes:
                snippet = _resume_snippet(skill_name, r)
                if snippet:
                    items.append(
                        EvidenceItem(
                            source_type="resume",
                            source_id=r.id,
                            source_label=r.title,
                            snippet=snippet,
                        )
                    )

            for repo in repos:
                snippet = _repo_snippet(skill_name, repo)
                if snippet:
                    items.append(
                        EvidenceItem(
                            source_type="repository",
                            source_id=repo.id,
                            source_label=f"{repo.owner}/{repo.name}",
                            snippet=snippet,
                        )
                    )

            confidence = _confidence(items)
            status = _classify(confidence)
            skills.append(
                SkillEvidence(
                    name=skill_name,
                    category=sr.category if sr else None,
                    importance=sr.importance if sr else None,
                    evidence=items,
                    best_snippet=_best_snippet(items),
                    confidence=round(confidence, 4),
                    status=status,
                )
            )

        # Sort by status (strong → weak → missing), then by importance desc.
        order = {"strong": 0, "weak": 1, "missing": 2}
        skills.sort(key=lambda s: (order[s.status], -(s.importance or 0), s.name.lower()))

        counts = {
            "strong": sum(1 for s in skills if s.status == "strong"),
            "weak": sum(1 for s in skills if s.status == "weak"),
            "missing": sum(1 for s in skills if s.status == "missing"),
        }
        return EvidenceReport(
            job_id=job.id,
            skills=skills,
            counts=counts,
            portfolio_count=len(portfolios),
            resume_count=len(resumes),
            repository_count=len(repos),
        )
