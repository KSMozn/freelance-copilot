from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---- Overview ----


class DashboardOverview(BaseModel):
    total_applications: int
    active_applications: int
    interviewed_count: int
    won_count: int
    completed_count: int
    lost_count: int
    total_revenue: Decimal | None
    average_contract_amount: Decimal | None
    average_opportunity_score: float | None
    average_proposal_quality_score: float | None


# ---- Funnel + outcome rates ----


class FunnelMetrics(BaseModel):
    applied: int
    viewed: int
    interview: int
    offer: int
    won: int
    completed: int


class OutcomeRates(BaseModel):
    """All rates are fractions in [0, 1]. Denominator is the count at the
    previous stage, so `interview_rate = interview / applied` etc.
    """

    viewed_rate: float | None
    interview_rate: float | None
    offer_rate: float | None
    win_rate: float | None
    completion_rate: float | None


# ---- Score / quality effectiveness ----


class BucketMetrics(BaseModel):
    """One row in a score- or quality-bucketed effectiveness table."""

    label: str
    applications: int
    interviews: int
    wins: int
    interview_rate: float | None
    win_rate: float | None
    average_quality_score: float | None
    average_contract_amount: Decimal | None


class ScoreEffectiveness(BaseModel):
    buckets: list[BucketMetrics]


class ProposalQualityEffectiveness(BaseModel):
    buckets: list[BucketMetrics]


# ---- Technology + domain + budget ----


class TechnologyPerformance(BaseModel):
    technology: str
    applications: int
    interviews: int
    wins: int
    win_rate: float | None
    average_opportunity_score: float | None
    average_proposal_quality_score: float | None


class DomainPerformance(BaseModel):
    domain: str
    applications: int
    interviews: int
    wins: int
    win_rate: float | None
    average_contract_amount: Decimal | None


class BudgetPerformance(BaseModel):
    bucket: str  # one of: unknown, under_250, 250_500, 500_1000, 1000_3000, 3000_plus
    applications: int
    interviews: int
    wins: int
    win_rate: float | None
    average_contract_amount: Decimal | None


# ---- Revenue + time-to-status ----


class MonthlyRevenuePoint(BaseModel):
    month: str  # YYYY-MM
    revenue: Decimal
    wins: int


class RevenueMetrics(BaseModel):
    total_revenue: Decimal
    completed_revenue: Decimal
    projected_revenue: Decimal  # won but not completed
    average_won_contract: Decimal | None
    largest_contract: Decimal | None
    revenue_by_month: list[MonthlyRevenuePoint]


class TimeToStatusBucket(BaseModel):
    label: str
    count: int
    avg_hours: float | None
    p50_hours: float | None
    p90_hours: float | None


class TimeToStatusMetrics(BaseModel):
    buckets: list[TimeToStatusBucket]


# ---- Recent activity ----


class RecentActivityEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: UUID
    job_title: str | None  # pulled from snapshot
    from_status: str | None
    to_status: str
    note: str | None
    created_at: datetime


class RecentActivity(BaseModel):
    items: list[RecentActivityEntry]


# ---- Top-level response ----


class AnalyticsRange(BaseModel):
    from_date: date | None = Field(default=None)
    to_date: date | None = Field(default=None)


class AnalyticsDashboardResponse(BaseModel):
    range: AnalyticsRange
    overview: DashboardOverview
    funnel: FunnelMetrics
    outcomes: OutcomeRates
    score_effectiveness: ScoreEffectiveness
    proposal_quality_effectiveness: ProposalQualityEffectiveness
    technologies: list[TechnologyPerformance]
    domains: list[DomainPerformance]
    budgets: list[BudgetPerformance]
    revenue: RevenueMetrics
    time_to_status: TimeToStatusMetrics
    recent_activity: RecentActivity
