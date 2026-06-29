"""Read-only analytics aggregations.

All inputs are immutable application snapshots + status timestamps +
application history. We never join back to mutable jobs / proposals / resumes
for analytical facts — that's the whole point of the Phase-6 snapshot.

Aggregations are computed in Python over the per-user application set. Per
the spec we explicitly avoid materialized views; the set is small (tens to
maybe a few hundred per user) and a single Postgres round-trip pulls it.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from statistics import mean
from typing import Any, Callable
from uuid import UUID

from app.application.dto.analytics_dto import (
    AnalyticsDashboardResponse,
    AnalyticsRange,
    BucketMetrics,
    BudgetPerformance,
    DashboardOverview,
    DomainPerformance,
    FunnelMetrics,
    MonthlyRevenuePoint,
    OutcomeRates,
    ProposalQualityEffectiveness,
    RecentActivity,
    RecentActivityEntry,
    RevenueMetrics,
    ScoreEffectiveness,
    TechnologyPerformance,
    TimeToStatusBucket,
    TimeToStatusMetrics,
)
from app.application.services.analytics_extraction import (
    BUDGET_BUCKETS_ORDER,
    QUALITY_BUCKETS,
    SCORE_BUCKETS,
    budget_bucket,
    extract_domain,
    extract_technologies,
    quality_bucket_label,
    score_bucket_label,
    snapshot_job_budget_text,
    snapshot_opportunity_score,
    snapshot_quality_score,
)
from app.domain.analytics.definitions import (
    is_active,
    is_completed,
    is_interviewed,
    is_lost,
    is_won,
)
from app.domain.entities.application import (
    Application,
    ApplicationHistoryEntry,
)
from app.domain.repositories.application_repository import (
    ApplicationHistoryRepository,
    ApplicationRepository,
)

RECENT_ACTIVITY_LIMIT = 10
TIME_TO_STATUS_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("applied_at", "viewed_at", "applied_to_viewed"),
    ("applied_at", "interview_at", "applied_to_interview"),
    ("interview_at", "offer_at", "interview_to_offer"),
    ("offer_at", "won_at", "offer_to_won"),
    ("won_at", "completed_at", "won_to_completed"),
)


# ---- Helpers ---------------------------------------------------------------


def _rate(numer: int, denom: int) -> float | None:
    if denom <= 0:
        return None
    return round(numer / denom, 4)


def _avg(values: list[float]) -> float | None:
    return round(mean(values), 4) if values else None


def _avg_decimal(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    return (sum(values, Decimal(0)) / Decimal(len(values))).quantize(Decimal("0.01"))


def _sum_decimal(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0.00")
    return sum(values, Decimal(0)).quantize(Decimal("0.01"))


def _percentile(values: list[float], pct: float) -> float | None:
    """Linear-interpolation percentile. `pct` in [0, 1]."""
    if not values:
        return None
    s = sorted(values)
    if len(s) == 1:
        return round(s[0], 4)
    k = (len(s) - 1) * pct
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    frac = k - lo
    return round(s[lo] + (s[hi] - s[lo]) * frac, 4)


def _hours_between(a: datetime | None, b: datetime | None) -> float | None:
    if a is None or b is None or b < a:
        return None
    return (b - a).total_seconds() / 3600.0


# ---- Section builders ------------------------------------------------------


def _overview(apps: list[Application]) -> DashboardOverview:
    contract_amounts = [a.contract_amount for a in apps if a.contract_amount is not None]
    revenue_apps = [a for a in apps if is_won(a) and a.contract_amount is not None]
    opp_scores = [
        snapshot_opportunity_score(a.snapshot)
        for a in apps
        if snapshot_opportunity_score(a.snapshot) is not None
    ]
    quality_scores = [
        snapshot_quality_score(a.snapshot)
        for a in apps
        if snapshot_quality_score(a.snapshot) is not None
    ]
    return DashboardOverview(
        total_applications=len(apps),
        active_applications=sum(1 for a in apps if is_active(a)),
        interviewed_count=sum(1 for a in apps if is_interviewed(a)),
        won_count=sum(1 for a in apps if is_won(a)),
        completed_count=sum(1 for a in apps if is_completed(a)),
        lost_count=sum(1 for a in apps if is_lost(a)),
        total_revenue=_sum_decimal([a.contract_amount for a in revenue_apps if a.contract_amount]),
        average_contract_amount=_avg_decimal(contract_amounts),
        average_opportunity_score=_avg([float(s) for s in opp_scores]),
        average_proposal_quality_score=_avg([float(s) for s in quality_scores]),
    )


def _funnel(apps: list[Application]) -> tuple[FunnelMetrics, OutcomeRates]:
    """Funnel counts use `*_at` timestamps, not the current status, so an
    application that's now `won` still counts toward `viewed`, `interview`,
    and `offer` if those timestamps were ever set.
    """
    applied = sum(1 for a in apps if a.applied_at is not None)
    viewed = sum(1 for a in apps if a.viewed_at is not None)
    interview = sum(1 for a in apps if a.interview_at is not None)
    offer = sum(1 for a in apps if a.offer_at is not None)
    won = sum(1 for a in apps if a.won_at is not None or is_won(a))
    completed = sum(1 for a in apps if is_completed(a))

    rates = OutcomeRates(
        viewed_rate=_rate(viewed, applied),
        interview_rate=_rate(interview, applied),
        offer_rate=_rate(offer, applied),
        win_rate=_rate(won, applied),
        completion_rate=_rate(completed, applied),
    )
    return (
        FunnelMetrics(
            applied=applied,
            viewed=viewed,
            interview=interview,
            offer=offer,
            won=won,
            completed=completed,
        ),
        rates,
    )


def _bucketed(
    apps: list[Application],
    bucket_fn: Callable[[Application], str | None],
    labels: tuple[str, ...],
) -> list[BucketMetrics]:
    by_bucket: dict[str, list[Application]] = {label: [] for label in labels}
    for a in apps:
        label = bucket_fn(a)
        if label is not None and label in by_bucket:
            by_bucket[label].append(a)
    out: list[BucketMetrics] = []
    for label in labels:
        bucket_apps = by_bucket[label]
        contract_amounts = [
            a.contract_amount for a in bucket_apps if a.contract_amount is not None
        ]
        quality_scores = [
            snapshot_quality_score(a.snapshot)
            for a in bucket_apps
            if snapshot_quality_score(a.snapshot) is not None
        ]
        interviews = sum(1 for a in bucket_apps if is_interviewed(a))
        wins = sum(1 for a in bucket_apps if is_won(a))
        out.append(
            BucketMetrics(
                label=label,
                applications=len(bucket_apps),
                interviews=interviews,
                wins=wins,
                interview_rate=_rate(interviews, len(bucket_apps)),
                win_rate=_rate(wins, len(bucket_apps)),
                average_quality_score=_avg([float(q) for q in quality_scores]),
                average_contract_amount=_avg_decimal(contract_amounts),
            )
        )
    return out


def _score_effectiveness(apps: list[Application]) -> ScoreEffectiveness:
    labels = tuple(label for _, _, label in SCORE_BUCKETS)
    return ScoreEffectiveness(
        buckets=_bucketed(
            apps,
            lambda a: score_bucket_label(snapshot_opportunity_score(a.snapshot)),
            labels,
        )
    )


def _quality_effectiveness(apps: list[Application]) -> ProposalQualityEffectiveness:
    labels = tuple(label for _, _, label in QUALITY_BUCKETS)
    return ProposalQualityEffectiveness(
        buckets=_bucketed(
            apps,
            lambda a: quality_bucket_label(snapshot_quality_score(a.snapshot)),
            labels,
        )
    )


def _technology_performance(apps: list[Application]) -> list[TechnologyPerformance]:
    by_tech: dict[str, list[Application]] = defaultdict(list)
    for a in apps:
        for tech in extract_technologies(a.snapshot):
            by_tech[tech].append(a)

    rows: list[TechnologyPerformance] = []
    for tech, bucket in by_tech.items():
        interviews = sum(1 for a in bucket if is_interviewed(a))
        wins = sum(1 for a in bucket if is_won(a))
        opp_scores = [
            snapshot_opportunity_score(a.snapshot)
            for a in bucket
            if snapshot_opportunity_score(a.snapshot) is not None
        ]
        quality_scores = [
            snapshot_quality_score(a.snapshot)
            for a in bucket
            if snapshot_quality_score(a.snapshot) is not None
        ]
        rows.append(
            TechnologyPerformance(
                technology=tech,
                applications=len(bucket),
                interviews=interviews,
                wins=wins,
                win_rate=_rate(wins, len(bucket)),
                average_opportunity_score=_avg([float(s) for s in opp_scores]),
                average_proposal_quality_score=_avg([float(s) for s in quality_scores]),
            )
        )
    # Sort by applications desc, then win_rate desc (None last), then name.
    rows.sort(
        key=lambda r: (
            -r.applications,
            -(r.win_rate or 0.0),
            r.technology.lower(),
        )
    )
    return rows


def _domain_performance(apps: list[Application]) -> list[DomainPerformance]:
    by_domain: dict[str, list[Application]] = defaultdict(list)
    for a in apps:
        domain = extract_domain(a.snapshot)
        if domain is None:
            continue
        by_domain[domain].append(a)

    rows: list[DomainPerformance] = []
    for domain, bucket in by_domain.items():
        interviews = sum(1 for a in bucket if is_interviewed(a))
        wins = sum(1 for a in bucket if is_won(a))
        contract_amounts = [
            a.contract_amount for a in bucket if a.contract_amount is not None
        ]
        rows.append(
            DomainPerformance(
                domain=domain,
                applications=len(bucket),
                interviews=interviews,
                wins=wins,
                win_rate=_rate(wins, len(bucket)),
                average_contract_amount=_avg_decimal(contract_amounts),
            )
        )
    rows.sort(
        key=lambda r: (
            -r.applications,
            -(r.win_rate or 0.0),
            r.domain.lower(),
        )
    )
    return rows


def _budget_performance(apps: list[Application]) -> list[BudgetPerformance]:
    by_bucket: dict[str, list[Application]] = {b: [] for b in BUDGET_BUCKETS_ORDER}
    for a in apps:
        bucket = budget_bucket(snapshot_job_budget_text(a.snapshot))
        by_bucket[bucket].append(a)

    rows: list[BudgetPerformance] = []
    for bucket in BUDGET_BUCKETS_ORDER:
        bucket_apps = by_bucket[bucket]
        interviews = sum(1 for a in bucket_apps if is_interviewed(a))
        wins = sum(1 for a in bucket_apps if is_won(a))
        contract_amounts = [
            a.contract_amount for a in bucket_apps if a.contract_amount is not None
        ]
        rows.append(
            BudgetPerformance(
                bucket=bucket,
                applications=len(bucket_apps),
                interviews=interviews,
                wins=wins,
                win_rate=_rate(wins, len(bucket_apps)) if bucket_apps else None,
                average_contract_amount=_avg_decimal(contract_amounts),
            )
        )
    return rows


def _revenue(apps: list[Application]) -> RevenueMetrics:
    won_apps = [a for a in apps if is_won(a) and a.contract_amount is not None]
    completed_apps = [a for a in won_apps if is_completed(a)]
    projected_apps = [a for a in won_apps if not is_completed(a)]

    by_month: dict[str, dict[str, Any]] = defaultdict(lambda: {"revenue": Decimal(0), "wins": 0})
    for a in won_apps:
        ts = a.completed_at or a.won_at
        if ts is None or a.contract_amount is None:
            continue
        key = ts.strftime("%Y-%m")
        by_month[key]["revenue"] += a.contract_amount
        by_month[key]["wins"] += 1

    monthly = [
        MonthlyRevenuePoint(
            month=key,
            revenue=Decimal(by_month[key]["revenue"]).quantize(Decimal("0.01")),
            wins=int(by_month[key]["wins"]),
        )
        for key in sorted(by_month.keys())
    ]

    largest = max(
        (a.contract_amount for a in won_apps if a.contract_amount is not None),
        default=None,
    )

    return RevenueMetrics(
        total_revenue=_sum_decimal([a.contract_amount for a in won_apps if a.contract_amount]),
        completed_revenue=_sum_decimal(
            [a.contract_amount for a in completed_apps if a.contract_amount]
        ),
        projected_revenue=_sum_decimal(
            [a.contract_amount for a in projected_apps if a.contract_amount]
        ),
        average_won_contract=_avg_decimal(
            [a.contract_amount for a in won_apps if a.contract_amount is not None]
        ),
        largest_contract=largest,
        revenue_by_month=monthly,
    )


def _time_to_status(apps: list[Application]) -> TimeToStatusMetrics:
    buckets: list[TimeToStatusBucket] = []
    for from_field, to_field, label in TIME_TO_STATUS_PAIRS:
        durations: list[float] = []
        for a in apps:
            hours = _hours_between(
                getattr(a, from_field), getattr(a, to_field)
            )
            if hours is not None:
                durations.append(hours)
        buckets.append(
            TimeToStatusBucket(
                label=label,
                count=len(durations),
                avg_hours=_avg(durations),
                p50_hours=_percentile(durations, 0.5),
                p90_hours=_percentile(durations, 0.9),
            )
        )
    return TimeToStatusMetrics(buckets=buckets)


def _recent_activity(
    history_rows: list[ApplicationHistoryEntry],
    apps: list[Application],
) -> RecentActivity:
    by_id: dict[UUID, Application] = {a.id: a for a in apps}
    items: list[RecentActivityEntry] = []
    for h in history_rows[:RECENT_ACTIVITY_LIMIT]:
        app = by_id.get(h.application_id)
        job_title: str | None = None
        if app and app.snapshot:
            raw = app.snapshot.get("job", {}).get("title") if isinstance(app.snapshot, dict) else None
            if isinstance(raw, str):
                job_title = raw
        items.append(
            RecentActivityEntry(
                application_id=h.application_id,
                job_title=job_title,
                from_status=h.from_status,
                to_status=h.to_status,
                note=h.note,
                created_at=h.created_at,
            )
        )
    return RecentActivity(items=items)


# ---- Service ---------------------------------------------------------------


class AnalyticsService:
    def __init__(
        self,
        *,
        application_repo: ApplicationRepository,
        history_repo: ApplicationHistoryRepository,
    ) -> None:
        self._apps = application_repo
        self._history = history_repo

    async def get_dashboard(
        self,
        *,
        user_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> AnalyticsDashboardResponse:
        apps = await self._apps.list_for_analytics(
            user_id, from_date=from_date, to_date=to_date
        )
        history = await self._history.list_recent_for_user(
            user_id, limit=RECENT_ACTIVITY_LIMIT
        )

        funnel, outcomes = _funnel(apps)

        return AnalyticsDashboardResponse(
            range=AnalyticsRange(
                from_date=from_date.date() if from_date else None,
                to_date=to_date.date() if to_date else None,
            ),
            overview=_overview(apps),
            funnel=funnel,
            outcomes=outcomes,
            score_effectiveness=_score_effectiveness(apps),
            proposal_quality_effectiveness=_quality_effectiveness(apps),
            technologies=_technology_performance(apps),
            domains=_domain_performance(apps),
            budgets=_budget_performance(apps),
            revenue=_revenue(apps),
            time_to_status=_time_to_status(apps),
            recent_activity=_recent_activity(history, apps),
        )
