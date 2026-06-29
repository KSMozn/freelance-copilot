"""Compact prompt context for proposal generation.

A pure-function builder that keeps prompts small and reproducible:

- Job title verbatim, description truncated to ~2500 chars at a word boundary
- Analysis: summary, top required skills, top risks, hidden requirements,
  deliverables
- Opportunity score + top-3 dimensions only
- Portfolio: top N matches with title, domain, matched skills, talking points
- Resume: best recommendation with title, role, primary skills,
  missing-or-weak skills, and positioning suggestions

The output is intentionally line-structured and label-marked so the mock AI
provider can parse it back out for tests, and so prompt diffs are reviewable.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.portfolio_dto import PortfolioMatchesResponse
from app.application.dto.resume_dto import ResumeRecommendationsResponse
from app.application.services.proposal_prompts import (
    OUTPUT_SCHEMA_BLOCK,
    USER_PROMPT_HEADER,
)
from app.domain.entities.analysis import JobAnalysis as DomainAnalysis
from app.domain.entities.analysis import OpportunityScore as DomainScore
from app.domain.entities.job import Job

MAX_JOB_DESCRIPTION_CHARS = 2500
MAX_REQUIRED_SKILLS = 8
MAX_RISKS = 3
MAX_HIDDEN_REQUIREMENTS = 3
MAX_DELIVERABLES = 4
MAX_SCORE_DIMENSIONS = 3
DEFAULT_TOP_PORTFOLIO = 2
DEFAULT_TOP_RESUME = 1


@dataclass(slots=True)
class ProposalContext:
    """Result of context-building. Held briefly, then serialized to a prompt."""

    user_prompt: str
    used_portfolio_ids: list
    used_resume_id: object | None


def _truncate_description(text: str, limit: int = MAX_JOB_DESCRIPTION_CHARS) -> str:
    """Cut at a word boundary, then add an ellipsis if anything was removed."""
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip()
    return cut + " …"


def _top_score_dimensions(score: DomainScore) -> list[tuple[str, int]]:
    items = list(score.score_breakdown.items())
    items.sort(key=lambda kv: kv[1], reverse=True)
    return items[:MAX_SCORE_DIMENSIONS]


def _bulleted(items: list[str]) -> str:
    return "\n".join(f"  - {item}" for item in items)


def build_proposal_user_prompt(
    *,
    job: Job,
    analysis: DomainAnalysis,
    score: DomainScore,
    portfolio_matches: PortfolioMatchesResponse,
    resume_recs: ResumeRecommendationsResponse,
    top_portfolio_n: int = DEFAULT_TOP_PORTFOLIO,
    top_resume_n: int = DEFAULT_TOP_RESUME,
) -> ProposalContext:
    used_portfolio_ids = []
    used_resume_id = None

    parts: list[str] = [USER_PROMPT_HEADER, ""]

    parts.append("--- JOB ---")
    parts.append(f"Title: {job.title}")
    parts.append("")
    parts.append("Description (truncated):")
    parts.append(_truncate_description(job.description))
    parts.append("")
    if analysis.summary:
        parts.append(f"Analysis summary: {analysis.summary}")
    if analysis.required_skills:
        parts.append(
            "Required skills: "
            + ", ".join(analysis.required_skills[:MAX_REQUIRED_SKILLS])
        )
    if analysis.hidden_requirements:
        parts.append("Hidden requirements:")
        parts.append(_bulleted(analysis.hidden_requirements[:MAX_HIDDEN_REQUIREMENTS]))
    if analysis.expected_deliverables:
        parts.append("Deliverables:")
        parts.append(_bulleted(analysis.expected_deliverables[:MAX_DELIVERABLES]))
    if analysis.risks:
        parts.append("Risks:")
        parts.append(
            "\n".join(
                f"  - {r.risk} ({r.severity}) — {r.mitigation}"
                for r in analysis.risks[:MAX_RISKS]
            )
        )
    parts.append("")
    parts.append(
        f"Opportunity score: {score.score}/100 "
        f"({score.recommendation}, confidence {score.confidence})"
    )
    top_dims = _top_score_dimensions(score)
    if top_dims:
        parts.append(
            "Top score dimensions: "
            + ", ".join(f"{k}={v}" for k, v in top_dims)
        )
    parts.append("")

    parts.append("--- PORTFOLIO MATCHES ---")
    if not portfolio_matches.matches:
        parts.append("(no portfolio projects available — do not invent any)")
    else:
        for i, m in enumerate(portfolio_matches.matches[:top_portfolio_n], start=1):
            used_portfolio_ids.append(m.portfolio_id)
            domain_part = (
                f" ({m.relevant_domains[0]})" if m.relevant_domains else ""
            )
            parts.append(f"{i}. {m.title}{domain_part}")
            if m.relevant_skills:
                parts.append("   Relevant skills: " + ", ".join(m.relevant_skills[:6]))
            if m.suggested_talking_points:
                parts.append("   Talking points:")
                for tp in m.suggested_talking_points[:3]:
                    parts.append(f"     • {tp}")
    parts.append("")

    parts.append("--- RECOMMENDED RESUME ---")
    if not resume_recs.recommendations:
        parts.append("(no resume profiles available)")
    else:
        top_resume = resume_recs.recommendations[:top_resume_n]
        if top_resume:
            best = top_resume[0]
            used_resume_id = best.resume_id
            parts.append(f"Title: {best.title}")
            if best.relevant_skills:
                parts.append("Primary skills: " + ", ".join(best.relevant_skills))
            if best.missing_or_weak_skills:
                parts.append(
                    "Missing or weak skills: "
                    + ", ".join(best.missing_or_weak_skills)
                )
            if best.suggested_positioning:
                parts.append("Positioning:")
                parts.append(_bulleted(best.suggested_positioning[:4]))
    parts.append("")

    parts.append(OUTPUT_SCHEMA_BLOCK)

    return ProposalContext(
        user_prompt="\n".join(parts),
        used_portfolio_ids=used_portfolio_ids,
        used_resume_id=used_resume_id,
    )
