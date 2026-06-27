"""Deterministic opportunity-scoring engine.

Each dimension is a pure function of the analysis + (optional) job metadata + the
FreelancerProfile. No hidden state, no IO — that lets us unit-test it exhaustively
and re-score historical analyses cheaply later.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.analysis_dto import JobAnalysisSchema
from app.domain.entities.job import Job
from app.domain.profiles.freelancer_profile import FreelancerProfile


@dataclass(slots=True)
class ScoringInput:
    job: Job
    analysis: JobAnalysisSchema


@dataclass(slots=True)
class ScoringResult:
    score: int
    recommendation: str
    confidence: str
    score_breakdown: dict[str, int]
    reasoning: str


def _norm(value: str) -> str:
    return value.strip().lower()


def _has_strong_signal(text: str | None, options: tuple[str, ...]) -> bool:
    if not text:
        return False
    haystack = _norm(text)
    return any(_norm(opt) in haystack for opt in options)


def _score_technical_fit(analysis: JobAnalysisSchema, profile: FreelancerProfile) -> int:
    """Up to 25. Proportion of required_skills the freelancer is strong at,
    with preferred_skills as a small bonus.
    """
    strong = {_norm(s) for s in profile.strong_skills}
    required = [_norm(s) for s in analysis.required_skills]
    preferred = [_norm(s) for s in analysis.preferred_skills]

    if not required and not preferred:
        return 12  # neutral

    req_matches = sum(1 for s in required if s in strong) if required else 0
    pref_matches = sum(1 for s in preferred if s in strong) if preferred else 0

    req_ratio = req_matches / len(required) if required else 0.0
    pref_ratio = pref_matches / len(preferred) if preferred else 0.0

    base = req_ratio * 22 if required else 18 * pref_ratio
    bonus = pref_ratio * 3 if required and preferred else 0
    return min(25, round(base + bonus))


def _score_domain_fit(analysis: JobAnalysisSchema, profile: FreelancerProfile) -> int:
    """Up to 10. Substring match against strong_domains, case-insensitive."""
    if not analysis.business_domain:
        return 4
    bd = _norm(analysis.business_domain)
    for d in profile.strong_domains:
        nd = _norm(d)
        if nd in bd or bd in nd:
            return 10
    return 2


def _score_proposal_count(job: Job) -> int:
    """Up to 20. Fewer proposals → easier to stand out."""
    n = job.proposal_count
    if n is None:
        return 10
    if n <= 5:
        return 20
    if n <= 10:
        return 16
    if n <= 20:
        return 12
    if n <= 30:
        return 8
    if n <= 50:
        return 4
    return 2


def _score_budget(analysis: JobAnalysisSchema) -> int:
    """Up to 10. From the analyzer's budget_assessment field."""
    return {"high": 10, "reasonable": 8, "low": 3, "unclear": 5}[analysis.budget_assessment]


def _score_client_quality(job: Job) -> int:
    """Up to 10. Placeholder — there is no client model wired up until Phase 3.

    Default to a neutral 7; bumped slightly when the job carries a source URL
    (a small signal that the freelancer at least kept the link / saw the client).
    """
    base = 6
    if job.source_url:
        base += 1
    return base


def _score_estimated_effort(analysis: JobAnalysisSchema) -> int:
    """Up to 10. Prefers jobs sized to 10–80 hours."""
    lo = analysis.estimated_hours_min
    hi = analysis.estimated_hours_max
    if lo is None or hi is None:
        return 5
    avg = (lo + hi) / 2
    if 10 <= avg <= 80:
        return 10
    if 5 <= avg < 10 or 80 < avg <= 120:
        return 7
    if avg < 5:
        return 3
    return 4


def _score_risk_level(analysis: JobAnalysisSchema) -> int:
    """Up to 10. From the analyzer's risk_level enum."""
    return {"low": 10, "medium": 6, "high": 2}[analysis.risk_level]


def _score_strategic_value(analysis: JobAnalysisSchema, profile: FreelancerProfile) -> int:
    """Up to 5. Counts strategic-priority keyword hits across the analysis."""
    haystack_parts: list[str] = []
    haystack_parts.extend(analysis.required_skills)
    haystack_parts.extend(analysis.technologies)
    if analysis.business_domain:
        haystack_parts.append(analysis.business_domain)
    if analysis.client_intent:
        haystack_parts.append(analysis.client_intent)
    haystack_parts.append(analysis.summary)
    haystack = _norm(" \n ".join(haystack_parts))

    hits = sum(1 for p in profile.strategic_priorities if _norm(p) in haystack)
    if hits == 0:
        return 0
    if hits == 1:
        return 2
    if hits == 2:
        return 4
    return 5


def _recommendation(score: int) -> str:
    if score >= 80:
        return "Strong Apply"
    if score >= 65:
        return "Apply"
    if score >= 50:
        return "Maybe"
    return "Skip"


def _confidence(job: Job, analysis: JobAnalysisSchema) -> str:
    """Roughly: how many input signals were non-empty?"""
    signals = 0
    if job.proposal_count is not None:
        signals += 1
    if analysis.budget_assessment != "unclear":
        signals += 1
    if analysis.required_skills:
        signals += 1
    if analysis.business_domain:
        signals += 1
    if analysis.estimated_hours_min is not None and analysis.estimated_hours_max is not None:
        signals += 1
    if analysis.risk_level:
        signals += 1
    if signals >= 5:
        return "high"
    if signals >= 3:
        return "medium"
    return "low"


def _reasoning(breakdown: dict[str, int], rec: str, profile: FreelancerProfile) -> str:
    """One-paragraph narrative summarising the strongest and weakest dimensions."""
    weights = profile.weights
    fractions = {k: (v / weights[k]) if weights.get(k) else 0.0 for k, v in breakdown.items()}
    best = sorted(fractions.items(), key=lambda kv: kv[1], reverse=True)[:2]
    worst = sorted(fractions.items(), key=lambda kv: kv[1])[:2]
    best_txt = ", ".join(k.replace("_", " ") for k, _ in best)
    worst_txt = ", ".join(k.replace("_", " ") for k, _ in worst)
    return (
        f"{rec}. Strongest signals: {best_txt}. "
        f"Weakest signals: {worst_txt}. "
        f"Scored against the {profile.version} profile."
    )


class ScoringService:
    """Pure, dependency-free scoring engine.

    Constructed once per request from the configured FreelancerProfile. Holds no
    state, so it can also be reused across requests if needed.
    """

    def __init__(self, profile: FreelancerProfile) -> None:
        self._profile = profile

    @property
    def profile_version(self) -> str:
        return self._profile.version

    def score(self, *, job: Job, analysis: JobAnalysisSchema) -> ScoringResult:
        breakdown = {
            "technical_fit": _score_technical_fit(analysis, self._profile),
            "domain_fit": _score_domain_fit(analysis, self._profile),
            "proposal_count": _score_proposal_count(job),
            "budget_attractiveness": _score_budget(analysis),
            "client_quality": _score_client_quality(job),
            "estimated_effort": _score_estimated_effort(analysis),
            "risk_level": _score_risk_level(analysis),
            "strategic_value": _score_strategic_value(analysis, self._profile),
        }
        total = sum(breakdown.values())
        rec = _recommendation(total)
        return ScoringResult(
            score=total,
            recommendation=rec,
            confidence=_confidence(job, analysis),
            score_breakdown=breakdown,
            reasoning=_reasoning(breakdown, rec, self._profile),
        )
