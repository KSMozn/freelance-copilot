"""Builds the JSONB snapshot stored on an application at submission time.

The snapshot is immutable on purpose: even if the underlying job, resume, or
portfolio rows are later edited or deleted, the snapshot preserves the exact
context the user applied with. Phase 8's learning loop depends on this.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.dto.portfolio_dto import PortfolioMatchesResponse
from app.application.dto.resume_dto import ResumeRecommendationsResponse
from app.domain.entities.analysis import OpportunityScore as DomainScore
from app.domain.entities.job import Job
from app.domain.entities.portfolio import Portfolio
from app.domain.entities.proposal import Proposal
from app.domain.entities.resume import Resume


def _job_snapshot(job: Job) -> dict[str, Any]:
    return {
        "id": str(job.id),
        "title": job.title,
        "url": job.source_url,
        "budget": _format_budget(job),
        "proposal_count": job.proposal_count,
        "status": str(job.status),
    }


def _format_budget(job: Job) -> str | None:
    if job.budget_min is None and job.budget_max is None:
        return None
    prefix = f"{job.budget_type} " if job.budget_type else ""
    if job.budget_min == job.budget_max and job.budget_min is not None:
        return f"{prefix}{job.currency} {job.budget_min}"
    return f"{prefix}{job.currency} {job.budget_min or '?'}–{job.budget_max or '?'}"


def _opportunity_snapshot(score: DomainScore | None) -> dict[str, Any] | None:
    if score is None:
        return None
    return {
        "score": score.score,
        "recommendation": score.recommendation,
        "confidence": score.confidence,
        "breakdown": dict(score.score_breakdown),
        "profile_version": score.profile_version,
    }


def _proposal_snapshot(proposal: Proposal) -> dict[str, Any]:
    return {
        "id": str(proposal.id),
        "title": proposal.title,
        "body": proposal.body,
        "short_body": proposal.short_body,
        "quality_score": proposal.quality_score,
        "quality_breakdown": dict(proposal.quality_breakdown or {}),
        "prompt_version": proposal.prompt_version,
        "model_provider": proposal.model_provider,
        "model_name": proposal.model_name,
    }


def _resume_snapshot(
    resume: Resume | None,
    recommendation_positioning: list[str] | None,
) -> dict[str, Any] | None:
    if resume is None:
        return None
    return {
        "id": str(resume.id),
        "title": resume.title,
        "target_role": resume.target_role,
        "seniority_level": resume.seniority_level,
        "primary_skills": list(resume.primary_skills),
        "suggested_positioning": list(recommendation_positioning or []),
    }


def _portfolio_snapshot(
    portfolios: list[Portfolio],
    match_data_by_id: dict[UUID, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in portfolios:
        match = match_data_by_id.get(p.id, {})
        out.append(
            {
                "id": str(p.id),
                "title": p.title,
                "business_domain": p.business_domain,
                "match_score": match.get("match_score"),
                "relevant_skills": match.get("relevant_skills", []),
                "talking_points": match.get("talking_points", []),
            }
        )
    return out


def build_snapshot(
    *,
    job: Job,
    score: DomainScore | None,
    proposal: Proposal,
    resume: Resume | None,
    portfolios: list[Portfolio],
    portfolio_matches: PortfolioMatchesResponse | None,
    resume_recs: ResumeRecommendationsResponse | None,
) -> dict[str, Any]:
    """Assemble the snapshot dict that becomes `applications.snapshot`."""
    match_data_by_id: dict[UUID, dict[str, Any]] = {}
    if portfolio_matches:
        for m in portfolio_matches.matches:
            match_data_by_id[m.portfolio_id] = {
                "match_score": m.match_score,
                "relevant_skills": list(m.relevant_skills),
                "talking_points": list(m.suggested_talking_points),
            }

    resume_positioning: list[str] | None = None
    if resume is not None and resume_recs is not None:
        for r in resume_recs.recommendations:
            if r.resume_id == resume.id:
                resume_positioning = list(r.suggested_positioning)
                break

    return {
        "job": _job_snapshot(job),
        "opportunity_score": _opportunity_snapshot(score),
        "proposal": _proposal_snapshot(proposal),
        "resume": _resume_snapshot(resume, resume_positioning),
        "portfolio": _portfolio_snapshot(portfolios, match_data_by_id),
    }
