"""CareerFitnessService — the dashboard payload assembler.

One service, one HTTP call (``GET /career-fitness``). Folds together:

  * `MarketSignalService` for demand counts + success/loss feedback +
    recurring gaps.
  * The user's `user_skills` pot (Phase B) so we can compute "you have
    this" vs "market wants it."
  * Their `repositories` rows (Phase 8) so we can suggest README
    enhancements per repo.

No new DB tables — Phase G computes on demand and renders on the
frontend.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.application.services.market_signal_service import (
    MarketSignalService,
    MarketSignals,
)
from app.domain.entities.analysis import JobAnalysis
from app.domain.entities.application import Application
from app.domain.entities.match_report import MatchReport
from app.domain.entities.repository import Repository
from app.domain.entities.skill_catalog import SkillCatalogEntry
from app.domain.entities.user_skill import UserSkillEntry


# ---- Dashboard DTO shape -------------------------------------------------


@dataclass(slots=True)
class MarketSkillRow:
    name: str
    market_count: float       # weighted demand across analyzed jobs
    raw_required: int
    raw_preferred: int
    in_your_pot: bool
    your_proficiency: int | None
    your_evidence_count: int


@dataclass(slots=True)
class SkillGap:
    """A skill the market wants but the user lacks (or has weakly)."""

    name: str
    market_count: float
    current_proficiency: int | None  # None = absent from pot
    severity: int  # 1 (mild) .. 5 (critical) — scaled by market weight


@dataclass(slots=True)
class FeedbackRow:
    name: str
    score: int  # win-weighted


@dataclass(slots=True)
class RecurringGapRow:
    name: str
    count: int
    avg_importance: float


@dataclass(slots=True)
class RepoSuggestion:
    """A nudge to surface skills already in a repo via README / metadata."""

    repository_id: str
    repository_name: str
    suggestion: str
    skills_covered: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CareerFitness:
    total_jobs_analyzed: int
    total_applications: int
    market_skills: list[MarketSkillRow]
    top_gaps: list[SkillGap]
    feedback: list[FeedbackRow]
    recurring_gaps: list[RecurringGapRow]
    repo_suggestions: list[RepoSuggestion]
    domain_demand: list[tuple[str, int]]


# ---- Service -------------------------------------------------------------


class CareerFitnessService:
    """Composes the dashboard payload. Stateless; safe per-request."""

    def __init__(self, market: MarketSignalService) -> None:
        self._market = market

    def compose(
        self,
        *,
        user_id: UUID,
        analyses: list[JobAnalysis],
        applications: list[Application],
        match_reports: list[MatchReport],
        repositories: list[Repository],
        user_skills: list[UserSkillEntry],
        catalog_by_id: dict[UUID, SkillCatalogEntry],
    ) -> CareerFitness:
        signals = self._market.compute(
            user_id=user_id,
            analyses=analyses,
            applications=applications,
            match_reports=match_reports,
            top_n=24,
        )

        # ---- Pot lookup keyed by lowercased canonical name ------------
        pot_by_name: dict[str, UserSkillEntry] = {}
        for row in user_skills:
            entry = catalog_by_id.get(row.skill_id)
            if entry is not None:
                pot_by_name[entry.name.lower()] = row

        # ---- Market skills table (have vs missing) --------------------
        market_skills: list[MarketSkillRow] = []
        for sd in signals.skill_demand:
            row = pot_by_name.get(sd.name.lower())
            market_skills.append(
                MarketSkillRow(
                    name=sd.name,
                    market_count=sd.count,
                    raw_required=sd.raw_required,
                    raw_preferred=sd.raw_preferred,
                    in_your_pot=row is not None and row.proficiency >= 1,
                    your_proficiency=row.proficiency if row else None,
                    your_evidence_count=row.evidence_count if row else 0,
                )
            )

        # ---- Top gaps (market wants, you lack / weak) -----------------
        top_gaps: list[SkillGap] = []
        for row in market_skills:
            # Treat "missing" as not in pot OR proficiency <= 2.
            current = row.your_proficiency
            if current is not None and current >= 3:
                continue
            # Severity: scale by market weight. The 12-cap keeps it bounded.
            severity = max(
                1, min(5, int(round(row.market_count / max(1.0, 12.0 / 5.0))))
            )
            top_gaps.append(
                SkillGap(
                    name=row.name,
                    market_count=row.market_count,
                    current_proficiency=current,
                    severity=severity,
                )
            )
        top_gaps.sort(key=lambda g: (-g.severity, -g.market_count, g.name.lower()))
        top_gaps = top_gaps[:10]

        # ---- Repo README suggestions ----------------------------------
        repo_suggestions: list[RepoSuggestion] = []
        market_skill_names = {row.name.lower() for row in market_skills if row.market_count >= 2}
        for repo in repositories:
            covered = sorted(
                {
                    s
                    for s in repo.derived_skills()
                    if isinstance(s, str) and s.lower() in market_skill_names
                }
            )
            if not covered:
                continue
            # Heuristic: if the architecture_summary is missing or under
            # 200 chars, suggest expanding the README around these skills.
            summary_len = len((repo.architecture_summary or "").strip())
            if summary_len >= 240:
                # Repo already documents itself well — skip the nudge to
                # avoid being noisy.
                continue
            suggestion = (
                f"This repo demonstrates {', '.join(covered[:4])}"
                + (f" (+{len(covered) - 4} more)" if len(covered) > 4 else "")
                + ". The README would convert better if it called these "
                "out by name with a short why-it-matters paragraph for each."
            )
            repo_suggestions.append(
                RepoSuggestion(
                    repository_id=str(repo.id),
                    repository_name=repo.name or repo.github_url or "Unnamed repo",
                    suggestion=suggestion,
                    skills_covered=covered[:8],
                )
            )
        repo_suggestions = repo_suggestions[:8]

        # ---- Feedback + recurring gaps mapped to DTO shape ------------
        feedback = [FeedbackRow(name=f.name, score=f.score) for f in signals.feedback]
        recurring = [
            RecurringGapRow(name=g.name, count=g.count, avg_importance=g.avg_importance)
            for g in signals.recurring_gaps
        ]
        domain_demand = [(d.name, d.count) for d in signals.domain_demand]

        return CareerFitness(
            total_jobs_analyzed=signals.total_jobs_analyzed,
            total_applications=signals.total_applications,
            market_skills=market_skills,
            top_gaps=top_gaps,
            feedback=feedback,
            recurring_gaps=recurring,
            repo_suggestions=repo_suggestions,
            domain_demand=domain_demand,
        )
