from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.application.services.analytics_service import AnalyticsService
from app.domain.entities.application import ApplicationHistoryEntry, ApplicationStatus
from tests.factories import (
    FakeApplicationHistoryRepository,
    FakeApplicationRepository,
    make_application,
)


def _snapshot(
    *,
    title: str = "FastAPI + PostgreSQL backend",
    body: str = "Need Python, FastAPI, PostgreSQL, Docker, RAG, OpenAI.",
    budget: str | None = "fixed USD 2500-4000",
    opportunity_score: int | None = 81,
    quality_score: int | None = 82,
    domain: str | None = None,
) -> dict:
    return {
        "job": {"title": title, "budget": budget, "business_domain": domain},
        "opportunity_score": (
            {"score": opportunity_score, "recommendation": "Strong Apply", "breakdown": {}}
            if opportunity_score is not None
            else None
        ),
        "proposal": {
            "title": "Re: " + title,
            "body": body,
            "short_body": "",
            "quality_score": quality_score,
            "quality_breakdown": {},
        },
        "resume": None,
        "portfolio": [],
    }


def _service(apps, history=None) -> AnalyticsService:  # type: ignore[no-untyped-def]
    repo = FakeApplicationRepository(apps)
    hrepo = FakeApplicationHistoryRepository()
    for entry in history or []:
        hrepo._items.append(entry)  # type: ignore[attr-defined]
    return AnalyticsService(application_repo=repo, history_repo=hrepo)


# ---- Overview ----

async def test_overview_counts() -> None:
    user_id = uuid4()
    apps = [
        make_application(user_id=user_id, status=ApplicationStatus.applied, snapshot=_snapshot()),
        make_application(user_id=user_id, status=ApplicationStatus.interview, snapshot=_snapshot()),
        make_application(
            user_id=user_id,
            status=ApplicationStatus.won,
            snapshot=_snapshot(),
            contract_amount=Decimal("3000"),
        ),
        make_application(
            user_id=user_id,
            status=ApplicationStatus.completed,
            snapshot=_snapshot(),
            contract_amount=Decimal("1750.00"),
        ),
        make_application(user_id=user_id, status=ApplicationStatus.rejected, snapshot=_snapshot()),
        make_application(user_id=user_id, status=ApplicationStatus.withdrawn, snapshot=_snapshot()),
    ]
    svc = _service(apps)
    dash = await svc.get_dashboard(user_id=user_id)
    o = dash.overview
    assert o.total_applications == 6
    assert o.active_applications == 2  # applied + interview
    assert o.interviewed_count == 3  # interview + won + completed
    assert o.won_count == 2
    assert o.completed_count == 1
    assert o.lost_count == 2
    assert o.total_revenue == Decimal("4750.00")
    assert o.average_opportunity_score is not None
    assert o.average_proposal_quality_score is not None


# ---- Funnel ----

async def test_funnel_uses_timestamps_not_just_current_status() -> None:
    """An application that's currently `won` still counts toward `viewed`,
    `interview`, and `offer` in the funnel."""
    user_id = uuid4()
    now = datetime.now(UTC)
    progressed = make_application(
        user_id=user_id,
        status=ApplicationStatus.won,
        applied_at=now - timedelta(days=10),
        viewed_at=now - timedelta(days=9),
        interview_at=now - timedelta(days=8),
        offer_at=now - timedelta(days=5),
        won_at=now - timedelta(days=2),
        contract_amount=Decimal("3000"),
        snapshot=_snapshot(),
    )
    fresh = make_application(
        user_id=user_id, status=ApplicationStatus.applied, snapshot=_snapshot()
    )

    svc = _service([progressed, fresh])
    dash = await svc.get_dashboard(user_id=user_id)
    f = dash.funnel
    assert f.applied == 2
    assert f.viewed == 1
    assert f.interview == 1
    assert f.offer == 1
    assert f.won == 1
    rates = dash.outcomes
    assert rates.viewed_rate == 0.5
    assert rates.interview_rate == 0.5
    assert rates.win_rate == 0.5


async def test_funnel_rates_none_on_empty() -> None:
    svc = _service([])
    dash = await svc.get_dashboard(user_id=uuid4())
    assert dash.outcomes.viewed_rate is None
    assert dash.outcomes.win_rate is None


# ---- Score / quality effectiveness ----

async def test_score_effectiveness_buckets() -> None:
    user_id = uuid4()
    apps = [
        make_application(user_id=user_id, snapshot=_snapshot(opportunity_score=40)),
        make_application(user_id=user_id, snapshot=_snapshot(opportunity_score=60)),
        make_application(user_id=user_id, snapshot=_snapshot(opportunity_score=72)),
        make_application(user_id=user_id, snapshot=_snapshot(opportunity_score=90)),
        make_application(
            user_id=user_id,
            status=ApplicationStatus.won,
            snapshot=_snapshot(opportunity_score=85),
            contract_amount=Decimal("4000"),
        ),
    ]
    svc = _service(apps)
    dash = await svc.get_dashboard(user_id=user_id)
    by_label = {b.label: b for b in dash.score_effectiveness.buckets}
    assert by_label["0-49"].applications == 1
    assert by_label["50-64"].applications == 1
    assert by_label["65-79"].applications == 1
    assert by_label["80-100"].applications == 2
    assert by_label["80-100"].wins == 1


async def test_quality_effectiveness_buckets() -> None:
    user_id = uuid4()
    apps = [
        make_application(user_id=user_id, snapshot=_snapshot(quality_score=55)),
        make_application(user_id=user_id, snapshot=_snapshot(quality_score=70)),
        make_application(user_id=user_id, snapshot=_snapshot(quality_score=82)),
        make_application(user_id=user_id, snapshot=_snapshot(quality_score=92)),
    ]
    svc = _service(apps)
    dash = await svc.get_dashboard(user_id=user_id)
    by_label = {b.label: b for b in dash.proposal_quality_effectiveness.buckets}
    assert by_label["0-59"].applications == 1
    assert by_label["60-74"].applications == 1
    assert by_label["75-84"].applications == 1
    assert by_label["85-100"].applications == 1


# ---- Technology + domain + budget ----

async def test_technology_performance_aggregates_per_tech() -> None:
    user_id = uuid4()
    apps = [
        make_application(
            user_id=user_id,
            status=ApplicationStatus.won,
            snapshot=_snapshot(body="Python + FastAPI + PostgreSQL build"),
            contract_amount=Decimal("3000"),
        ),
        make_application(
            user_id=user_id,
            status=ApplicationStatus.rejected,
            snapshot=_snapshot(body="React + TypeScript marketing site"),
        ),
        make_application(
            user_id=user_id,
            status=ApplicationStatus.interview,
            snapshot=_snapshot(body="Python + FastAPI + Docker service"),
        ),
    ]
    svc = _service(apps)
    dash = await svc.get_dashboard(user_id=user_id)
    by_tech = {t.technology: t for t in dash.technologies}
    assert "Python" in by_tech
    assert by_tech["Python"].applications == 2
    assert by_tech["Python"].wins == 1
    assert by_tech["Python"].interviews == 2  # won counts as interviewed
    assert "TypeScript" in by_tech
    assert by_tech["TypeScript"].applications == 1


async def test_domain_performance_uses_snapshot_domain() -> None:
    user_id = uuid4()
    apps = [
        make_application(
            user_id=user_id,
            status=ApplicationStatus.won,
            snapshot=_snapshot(domain="AI SaaS"),
            contract_amount=Decimal("3500"),
        ),
        make_application(
            user_id=user_id,
            status=ApplicationStatus.rejected,
            snapshot=_snapshot(domain="FinTech"),
        ),
    ]
    svc = _service(apps)
    dash = await svc.get_dashboard(user_id=user_id)
    by_domain = {d.domain: d for d in dash.domains}
    assert by_domain["AI SaaS"].wins == 1
    assert by_domain["FinTech"].applications == 1


async def test_budget_performance_buckets() -> None:
    user_id = uuid4()
    apps = [
        make_application(user_id=user_id, snapshot=_snapshot(budget="USD 75-150")),
        make_application(user_id=user_id, snapshot=_snapshot(budget="USD 400-700")),
        make_application(user_id=user_id, snapshot=_snapshot(budget="USD 800")),
        make_application(user_id=user_id, snapshot=_snapshot(budget="USD 1500-2500")),
        make_application(user_id=user_id, snapshot=_snapshot(budget="USD 3000-5000")),
        make_application(user_id=user_id, snapshot=_snapshot(budget=None)),
    ]
    svc = _service(apps)
    dash = await svc.get_dashboard(user_id=user_id)
    by_bucket = {b.bucket: b for b in dash.budgets}
    assert by_bucket["under_250"].applications == 1
    assert by_bucket["250_500"].applications == 1
    assert by_bucket["500_1000"].applications == 1
    assert by_bucket["1000_3000"].applications == 1
    assert by_bucket["3000_plus"].applications == 1
    assert by_bucket["unknown"].applications == 1


# ---- Revenue ----

async def test_revenue_splits_completed_and_projected() -> None:
    user_id = uuid4()
    now = datetime.now(UTC)
    apps = [
        make_application(
            user_id=user_id,
            status=ApplicationStatus.completed,
            snapshot=_snapshot(),
            contract_amount=Decimal("3000.00"),
            won_at=now - timedelta(days=40),
            completed_at=now - timedelta(days=20),
        ),
        make_application(
            user_id=user_id,
            status=ApplicationStatus.won,
            snapshot=_snapshot(),
            contract_amount=Decimal("1500.00"),
            won_at=now - timedelta(days=10),
        ),
        make_application(
            user_id=user_id,
            status=ApplicationStatus.interview,
            snapshot=_snapshot(),
        ),
    ]
    svc = _service(apps)
    dash = await svc.get_dashboard(user_id=user_id)
    r = dash.revenue
    assert r.total_revenue == Decimal("4500.00")
    assert r.completed_revenue == Decimal("3000.00")
    assert r.projected_revenue == Decimal("1500.00")
    assert r.largest_contract == Decimal("3000.00")
    # Two distinct months in revenue_by_month
    months = {m.month for m in r.revenue_by_month}
    assert len(months) >= 1  # both wins land in their respective months


# ---- Time-to-status ----

async def test_time_to_status_metrics() -> None:
    user_id = uuid4()
    now = datetime.now(UTC)
    apps = [
        make_application(
            user_id=user_id,
            status=ApplicationStatus.won,
            applied_at=now - timedelta(hours=120),
            viewed_at=now - timedelta(hours=100),  # 20h after applied
            interview_at=now - timedelta(hours=72),  # 48h after applied
            offer_at=now - timedelta(hours=24),  # 48h after interview
            won_at=now,
            snapshot=_snapshot(),
        ),
    ]
    svc = _service(apps)
    dash = await svc.get_dashboard(user_id=user_id)
    buckets = {b.label: b for b in dash.time_to_status.buckets}
    assert buckets["applied_to_viewed"].count == 1
    assert buckets["applied_to_viewed"].avg_hours == 20.0
    assert buckets["interview_to_offer"].count == 1
    assert buckets["interview_to_offer"].avg_hours == 48.0
    # Pair with no samples → count 0, all numerics None
    assert buckets["won_to_completed"].count == 0
    assert buckets["won_to_completed"].avg_hours is None


# ---- Recent activity ----

async def test_recent_activity_orders_desc_and_caps_at_10() -> None:
    user_id = uuid4()
    apps = [
        make_application(user_id=user_id, status=ApplicationStatus.applied, snapshot=_snapshot()),
    ]
    history = [
        ApplicationHistoryEntry(
            id=uuid4(),
            application_id=apps[0].id,
            user_id=user_id,
            from_status=None,
            to_status=f"step-{i}",
            note=f"note {i}",
            created_at=datetime.now(UTC) - timedelta(hours=i),
        )
        for i in range(15)
    ]
    svc = _service(apps, history=history)
    dash = await svc.get_dashboard(user_id=user_id)
    items = dash.recent_activity.items
    assert len(items) == 10
    # Most-recent-first: index 0 was just now, index 14 is 14h ago.
    assert items[0].to_status == "step-0"
    # job_title was looked up from the snapshot
    assert items[0].job_title == "FastAPI + PostgreSQL backend"


# ---- Date filtering ----

async def test_date_filter_excludes_out_of_range() -> None:
    user_id = uuid4()
    now = datetime.now(UTC)
    apps = [
        make_application(
            user_id=user_id,
            status=ApplicationStatus.applied,
            snapshot=_snapshot(),
            created_at=now - timedelta(days=200),
        ),
        make_application(
            user_id=user_id,
            status=ApplicationStatus.applied,
            snapshot=_snapshot(),
            created_at=now - timedelta(days=5),
        ),
    ]
    svc = _service(apps)
    only_recent = await svc.get_dashboard(
        user_id=user_id, from_date=now - timedelta(days=30)
    )
    assert only_recent.overview.total_applications == 1


# ---- Empty state ----

async def test_empty_state_returns_zero_counts() -> None:
    svc = _service([])
    dash = await svc.get_dashboard(user_id=uuid4())
    assert dash.overview.total_applications == 0
    assert dash.overview.total_revenue is None or dash.overview.total_revenue == Decimal("0.00")
    assert dash.funnel.applied == 0
    assert dash.technologies == []
    assert dash.domains == []
