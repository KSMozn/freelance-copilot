"""Auth gating + happy-path API tests for the analytics dashboard."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.services.analytics_service import AnalyticsService
from app.core.deps import get_analytics_service, get_current_user
from app.domain.entities.application import ApplicationStatus
from app.domain.entities.user import User
from app.main import app
from tests.factories import (
    FakeApplicationHistoryRepository,
    FakeApplicationRepository,
    make_application,
)


@pytest.fixture
def user() -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        email="api-test@example.com",
        password_hash="x",
        full_name="Tester",
        is_active=True,
        is_superuser=False,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def client(user: User):  # type: ignore[no-untyped-def]
    snapshot = {
        "job": {"title": "FastAPI + PostgreSQL backend", "budget": "USD 2500-4000"},
        "opportunity_score": {"score": 82, "recommendation": "Strong Apply", "breakdown": {}},
        "proposal": {
            "title": "Re: FastAPI build",
            "body": "Python + FastAPI + PostgreSQL build for an AI SaaS team.",
            "short_body": "Python + FastAPI + PostgreSQL.",
            "quality_score": 82,
            "quality_breakdown": {},
        },
        "resume": None,
        "portfolio": [],
    }
    apps = [
        make_application(
            user_id=user.id,
            status=ApplicationStatus.won,
            snapshot=snapshot,
            contract_amount=Decimal("3000.00"),
        ),
        make_application(
            user_id=user.id,
            status=ApplicationStatus.rejected,
            snapshot=snapshot,
        ),
    ]
    app_repo = FakeApplicationRepository(apps)
    history_repo = FakeApplicationHistoryRepository()

    def _service() -> AnalyticsService:
        return AnalyticsService(application_repo=app_repo, history_repo=history_repo)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_analytics_service] = _service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_dashboard_requires_auth() -> None:
    with TestClient(app) as raw:
        assert raw.get("/api/v1/analytics/dashboard").status_code == 401


def test_dashboard_returns_full_payload(client: TestClient) -> None:
    resp = client.get("/api/v1/analytics/dashboard")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Top-level shape
    assert "overview" in body
    assert "funnel" in body
    assert "outcomes" in body
    assert "score_effectiveness" in body
    assert "proposal_quality_effectiveness" in body
    assert "technologies" in body
    assert "domains" in body
    assert "budgets" in body
    assert "revenue" in body
    assert "time_to_status" in body
    assert "recent_activity" in body
    # Values
    o = body["overview"]
    assert o["total_applications"] == 2
    assert o["won_count"] == 1
    assert o["lost_count"] == 1
    assert o["total_revenue"] == "3000.00"


def test_dashboard_accepts_date_range(client: TestClient) -> None:
    # Tomorrow → tomorrow filters out both seeded apps.
    tomorrow = (datetime.now(UTC).date()).isoformat()
    far_future = "2099-12-31"
    resp = client.get(
        f"/api/v1/analytics/dashboard?from_date={far_future}&to_date={far_future}"
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["overview"]["total_applications"] == 0
    assert resp.json()["range"]["from_date"] == far_future
    assert resp.json()["range"]["to_date"] == far_future
    # tomorrow alone shouldn't error
    resp2 = client.get(f"/api/v1/analytics/dashboard?from_date={tomorrow}")
    assert resp2.status_code == 200


def test_dashboard_handles_empty_user(client: TestClient, user: User) -> None:  # type: ignore[no-untyped-def]
    # Override to a different user with no apps.
    new_user = User(
        id=uuid4(),
        email="empty@example.com",
        password_hash="x",
        full_name=None,
        is_active=True,
        is_superuser=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    app.dependency_overrides[get_current_user] = lambda: new_user
    resp = client.get("/api/v1/analytics/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert body["overview"]["total_applications"] == 0
    assert body["technologies"] == []
    assert body["domains"] == []
