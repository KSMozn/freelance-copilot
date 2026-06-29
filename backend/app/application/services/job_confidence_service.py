"""Multi-dimensional confidence: will this proposal land?

Pure composition over existing services — no LLM. Reuses:
  - SkillEvidenceService for the technical-coverage signal
  - PortfolioMatchingService + RepositoryMatchingService for domain + semantic
  - OpportunityScoreRepository for the recommendation tier blend

The numbers shown here are decision-support, not deterministic guarantees —
the interview-chance bucket is derived from `overall_match` and the existing
opportunity score, both of which fold through several heuristics already.
"""
from __future__ import annotations

from uuid import UUID

from app.application.dto.confidence_dto import JobConfidenceReport
from app.application.dto.evidence_dto import EvidenceReport, SkillEvidence
from app.application.services.portfolio_matching_service import (
    PortfolioMatchingService,
)
from app.application.services.repository_matching_service import (
    RepositoryMatchingService,
)
from app.application.services.skill_evidence_service import SkillEvidenceService
from app.domain.repositories.analysis_repository import OpportunityScoreRepository

DEFAULT_IMPORTANCE = 3  # used when evidence has no importance attached


def _technical_match(evidence: EvidenceReport) -> int:
    """Importance-weighted coverage: each skill contributes its importance
    times a status multiplier; we report the fraction of the max possible.
    """
    if not evidence.skills:
        return 0
    status_weight = {"strong": 1.0, "weak": 0.5, "missing": 0.0}
    earned = 0.0
    possible = 0.0
    for s in evidence.skills:
        weight = float(s.importance or DEFAULT_IMPORTANCE)
        possible += weight
        earned += weight * status_weight[s.status]
    if possible == 0:
        return 0
    return round((earned / possible) * 100)


def _critical_missing(evidence: EvidenceReport, *, threshold: int = 4) -> list[str]:
    """Missing skills the analyzer marked as important (≥ threshold stars).

    Falls back to ALL missing skills if no importance metadata is available
    (older analyses without `stack_requirements`).
    """
    important: list[SkillEvidence] = [
        s
        for s in evidence.skills
        if s.status == "missing" and (s.importance or 0) >= threshold
    ]
    if not important:
        important = [s for s in evidence.skills if s.status == "missing"]
    important.sort(key=lambda s: (-(s.importance or 0), s.name.lower()))
    return [s.name for s in important[:6]]


def _bucket_interview(overall: int, opportunity_score: int | None) -> str:
    """Blend the new overall_match with the existing 0–100 opportunity score
    (analysis + scoring engine). Both contribute equally — neither alone is
    enough to predict whether the client will read the proposal.
    """
    if opportunity_score is None:
        blended = overall
    else:
        blended = round(0.6 * overall + 0.4 * opportunity_score)
    if blended >= 75:
        return "high"
    if blended >= 55:
        return "medium"
    return "low"


def _rationale(
    *,
    technical: int,
    domain: int,
    architecture: int,
    overall: int,
    missing: list[str],
    has_portfolio_match: bool,
    has_repo_match: bool,
) -> list[str]:
    out: list[str] = []
    if technical >= 80:
        out.append("Strong technical coverage — most required skills have concrete evidence.")
    elif technical >= 50:
        out.append("Partial technical coverage — several skills only have listing-level evidence.")
    else:
        out.append("Thin technical coverage — call this out honestly in the proposal.")

    if architecture >= 75:
        out.append("Architecturally adjacent to past work — lean on the semantic match.")
    elif architecture >= 50:
        out.append("Moderate architectural overlap — pick one project as the closest analogue.")

    if domain >= 75:
        out.append("Same business domain — frame your experience in that vertical.")
    elif domain >= 30:
        out.append("Adjacent domain — bridge it explicitly rather than ignore the gap.")

    if missing:
        head = ", ".join(missing[:3])
        out.append(f"Missing or weak: {head}. Acknowledge briefly; do not dwell.")
    if not has_portfolio_match and not has_repo_match:
        out.append("No portfolio or scanned-repo evidence loaded — add some to lift confidence.")
    return out[:5]


class JobConfidenceService:
    def __init__(
        self,
        *,
        evidence_service: SkillEvidenceService,
        portfolio_matching: PortfolioMatchingService,
        repository_matching: RepositoryMatchingService,
        score_repo: OpportunityScoreRepository,
    ) -> None:
        self._evidence = evidence_service
        self._portfolios = portfolio_matching
        self._repos = repository_matching
        self._scores = score_repo

    async def build(self, *, user_id: UUID, job_id: UUID) -> JobConfidenceReport:
        # `build` itself raises NotFoundError if analysis is missing — let it
        # propagate so the endpoint can return 404 with a meaningful message.
        evidence = await self._evidence.build(user_id=user_id, job_id=job_id)
        portfolio_matches = await self._portfolios.match(
            user_id=user_id, job_id=job_id, top_n=3
        )
        repo_matches = await self._repos.match(
            user_id=user_id, job_id=job_id, top_n=3
        )

        # Best-of: take the strongest signal across portfolios + repos.
        top_portfolio = portfolio_matches.matches[0] if portfolio_matches.matches else None
        top_repo = repo_matches.matches[0] if repo_matches.matches else None

        semantic_pool = [m.semantic_score for m in (top_portfolio, top_repo) if m]
        domain_pool = [m.domain_overlap_score for m in (top_portfolio, top_repo) if m]

        architecture = round(max(semantic_pool) * 100) if semantic_pool else 0
        domain = round(max(domain_pool) * 100) if domain_pool else 0
        technical = _technical_match(evidence)

        # Overall: technical is the strongest signal because it's the most
        # concrete (per-skill evidence), then architecture (semantic), then
        # domain (binary-ish). Coefficients sum to 1.0.
        overall = round(0.5 * technical + 0.3 * architecture + 0.2 * domain)
        overall = max(0, min(100, overall))

        opportunity = await self._scores.get_by_job_id(job_id)
        interview = _bucket_interview(overall, opportunity.score if opportunity else None)

        missing = _critical_missing(evidence)
        rationale = _rationale(
            technical=technical,
            domain=domain,
            architecture=architecture,
            overall=overall,
            missing=missing,
            has_portfolio_match=top_portfolio is not None,
            has_repo_match=top_repo is not None,
        )

        return JobConfidenceReport(
            job_id=job_id,
            overall_match=overall,
            technical_match=technical,
            domain_match=domain,
            architecture_match=architecture,
            missing_critical_skills=missing,
            interview_chance=interview,  # type: ignore[arg-type]
            rationale=rationale,
        )
