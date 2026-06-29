"""MarketSignalService — compute-on-demand demand signals from the user's corpus.

Walks every job analysis the user has imported (and every application's
outcome) to produce a snapshot of what THEIR market is asking for. No
new tables — everything is derived from already-stored data, so the
signals stay fresh on every dashboard load.

Key outputs:
  * ``skill_demand``: how many of the user's analyzed jobs cited each skill.
    Required skills weight more than preferred skills.
  * ``domain_demand``: count per business_domain.
  * ``success_signal``: skills appearing in WON / COMPLETED applications.
    These are positive signals — what gets you hired.
  * ``loss_signal``: skills appearing in LOST applications (with normal
    weight). Subtracted from `success_signal` to bias for "wins."
  * ``recurring_gaps``: skills missing across match_reports — what keeps
    flagging as critical and missing.

Phase G ships the pure derivation. Phase G.1 can persist snapshots if
the dashboard becomes hot.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from app.domain.analytics.definitions import LOST_STATUSES, WON_STATUSES
from app.domain.entities.application import Application
from app.domain.entities.analysis import JobAnalysis
from app.domain.entities.match_report import MatchReport


# Required skills carry more weight than preferred. Weights are normalized
# so the dashboard's "demand counter" stays interpretable.
_REQUIRED_WEIGHT = 1.0
_PREFERRED_WEIGHT = 0.5

# Success/loss feedback weights — applied per skill mention in a job whose
# application landed in the corresponding status set.
_WON_WEIGHT = 3
_INTERVIEW_WEIGHT = 1
_LOST_WEIGHT = -1


@dataclass(slots=True)
class SkillDemand:
    name: str
    count: float  # weighted across required vs preferred
    raw_required: int
    raw_preferred: int


@dataclass(slots=True)
class DomainDemand:
    name: str
    count: int


@dataclass(slots=True)
class FeedbackSignal:
    name: str
    score: int  # win-weighted; positive = pulls in, negative = poison


@dataclass(slots=True)
class RecurringGap:
    name: str
    count: int  # how many match_reports flagged this skill missing/weak
    avg_importance: float


@dataclass(slots=True)
class MarketSignals:
    total_jobs_analyzed: int
    total_applications: int
    skill_demand: list[SkillDemand]
    domain_demand: list[DomainDemand]
    feedback: list[FeedbackSignal]
    recurring_gaps: list[RecurringGap]


def _normalize(name: str) -> str:
    return (name or "").strip()


def _bucket_skills(items: Iterable[str]) -> Counter[str]:
    c: Counter[str] = Counter()
    for raw in items or []:
        n = _normalize(raw)
        if n:
            c[n] += 1
    return c


class MarketSignalService:
    """Pure computation — no DB writes. Inject the data via plain lists."""

    def compute(
        self,
        *,
        user_id: UUID,
        analyses: list[JobAnalysis],
        applications: list[Application],
        match_reports: list[MatchReport],
        top_n: int = 20,
    ) -> MarketSignals:
        # ---- Build a job_id → analysis index so we can look up by app ----
        analysis_by_job: dict[UUID, JobAnalysis] = {a.job_id: a for a in analyses}

        # ---- Skill demand (weighted required vs preferred) ----
        required_counts: Counter[str] = Counter()
        preferred_counts: Counter[str] = Counter()
        domain_counts: Counter[str] = Counter()
        for a in analyses:
            required_counts.update(_bucket_skills(a.required_skills or []))
            preferred_counts.update(_bucket_skills(a.preferred_skills or []))
            if a.business_domain:
                domain_counts[_normalize(a.business_domain)] += 1

        all_skill_names = set(required_counts) | set(preferred_counts)
        skill_demand: list[SkillDemand] = []
        for name in all_skill_names:
            req = required_counts.get(name, 0)
            pref = preferred_counts.get(name, 0)
            score = _REQUIRED_WEIGHT * req + _PREFERRED_WEIGHT * pref
            skill_demand.append(
                SkillDemand(
                    name=name, count=score, raw_required=req, raw_preferred=pref
                )
            )
        skill_demand.sort(key=lambda s: (-s.count, s.name.lower()))

        # ---- Feedback loop from applications ----
        feedback_counts: Counter[str] = Counter()
        for app in applications:
            analysis = analysis_by_job.get(app.job_id)
            if analysis is None:
                continue
            mentions = (analysis.required_skills or []) + (analysis.preferred_skills or [])
            mentions = [_normalize(s) for s in mentions if _normalize(s)]
            weight = _status_weight(app.status)
            if weight == 0:
                continue
            for name in mentions:
                feedback_counts[name] += weight
        feedback = [
            FeedbackSignal(name=n, score=s)
            for n, s in feedback_counts.items()
            if s != 0
        ]
        feedback.sort(key=lambda f: (-f.score, f.name.lower()))

        # ---- Recurring gaps from match_reports ----
        gap_counts: Counter[str] = Counter()
        importance_sum: Counter[str] = Counter()
        importance_n: Counter[str] = Counter()
        for report in match_reports:
            for item in report.missing_critical_skills or []:
                if not isinstance(item, dict):
                    continue
                name = _normalize(str(item.get("name", "")))
                if not name:
                    continue
                gap_counts[name] += 1
                imp = int(item.get("importance") or 3)
                importance_sum[name] += imp
                importance_n[name] += 1
        recurring_gaps = [
            RecurringGap(
                name=name,
                count=count,
                avg_importance=(
                    importance_sum[name] / importance_n[name]
                    if importance_n[name]
                    else 3.0
                ),
            )
            for name, count in gap_counts.items()
        ]
        recurring_gaps.sort(
            key=lambda g: (-g.count, -g.avg_importance, g.name.lower())
        )

        domain_demand = [
            DomainDemand(name=n, count=c) for n, c in domain_counts.items()
        ]
        domain_demand.sort(key=lambda d: (-d.count, d.name.lower()))

        return MarketSignals(
            total_jobs_analyzed=len(analyses),
            total_applications=len(applications),
            skill_demand=skill_demand[:top_n],
            domain_demand=domain_demand[: max(10, top_n // 2)],
            feedback=feedback[:top_n],
            recurring_gaps=recurring_gaps[:top_n],
        )


def _status_weight(status: object) -> int:
    """Translate an application status into a feedback signal weight."""
    # ApplicationStatus is an enum elsewhere — guard with str() so we accept
    # both the enum and its string serialization.
    s = getattr(status, "value", status)
    if s in {st.value for st in WON_STATUSES}:
        return _WON_WEIGHT
    if s in {st.value for st in LOST_STATUSES}:
        return _LOST_WEIGHT
    if s == "interview":
        return _INTERVIEW_WEIGHT
    return 0
