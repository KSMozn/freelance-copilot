"""API-level tests with dependency overrides — no real Postgres needed.

Verifies:
- /analyze and /analysis require auth (401 without a token).
- /analyze returns a valid JobAnalysisResponse payload when authenticated.
- /analysis returns 404 before /analyze has run.
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.services.job_analysis_service import JobAnalysisService
from app.application.services.scoring_service import ScoringService
from app.core.deps import get_current_user, get_job_analysis_service
from app.domain.entities.user import User
from app.domain.profiles.freelancer_profile import DEFAULT_FREELANCER_PROFILE
from app.infrastructure.ai.mock_provider import MockAIProvider
from app.main import app
from tests.factories import (
    FakeAnalysisRepository,
    FakeJobRepository,
    FakeScoreRepository,
    make_job,
)


@pytest.fixture
def user() -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        email="api-test@example.com",
        password_hash="not-used",
        full_name="API Test",
        is_active=True,
        is_superuser=False,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def job(user: User):
    return make_job(
        user_id=user.id,
        title="Python + FastAPI backend with RAG",
        description=(
            "Need Python, FastAPI, PostgreSQL, Docker. AI SaaS company. Long term."
        ),
        proposal_count=5,
    )


@pytest.fixture
def client(user: User, job) -> TestClient:  # type: ignore[no-untyped-def]
    job_repo = FakeJobRepository([job])
    analysis_repo = FakeAnalysisRepository()
    score_repo = FakeScoreRepository()

    def _service() -> JobAnalysisService:
        return JobAnalysisService(
            job_repo=job_repo,
            analysis_repo=analysis_repo,
            score_repo=score_repo,
            ai_provider=MockAIProvider(),
            scoring=ScoringService(DEFAULT_FREELANCER_PROFILE),
        )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_job_analysis_service] = _service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_analyze_requires_auth(job) -> None:  # type: ignore[no-untyped-def]
    # No overrides → real auth dep runs → 401
    with TestClient(app) as raw:
        resp = raw.post(f"/api/v1/jobs/{job.id}/analyze")
        assert resp.status_code == 401


def test_get_analysis_requires_auth(job) -> None:  # type: ignore[no-untyped-def]
    with TestClient(app) as raw:
        resp = raw.get(f"/api/v1/jobs/{job.id}/analysis")
        assert resp.status_code == 401


def test_analyze_returns_full_payload(client: TestClient, job) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(f"/api/v1/jobs/{job.id}/analyze")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # analysis shape
    a = body["analysis"]
    assert a["job_id"] == str(job.id)
    assert a["provider"] == "mock"
    assert isinstance(a["required_skills"], list)
    assert "summary" in a

    # score shape
    s = body["score"]
    assert 0 <= s["score"] <= 100
    assert s["recommendation"] in ("Strong Apply", "Apply", "Maybe", "Skip")
    assert s["confidence"] in ("high", "medium", "low")
    assert set(s["score_breakdown"].keys()) == {
        "technical_fit",
        "domain_fit",
        "proposal_count",
        "budget_attractiveness",
        "client_quality",
        "estimated_effort",
        "risk_level",
        "strategic_value",
    }
    assert sum(s["score_breakdown"].values()) == s["score"]


def test_get_analysis_before_analyze_returns_404(client: TestClient, job) -> None:  # type: ignore[no-untyped-def]
    resp = client.get(f"/api/v1/jobs/{job.id}/analysis")
    assert resp.status_code == 404


def test_get_analysis_after_analyze_returns_200(client: TestClient, job) -> None:  # type: ignore[no-untyped-def]
    client.post(f"/api/v1/jobs/{job.id}/analyze")
    resp = client.get(f"/api/v1/jobs/{job.id}/analysis")
    assert resp.status_code == 200
    assert resp.json()["analysis"]["job_id"] == str(job.id)


def test_analyze_unknown_job_returns_404(client: TestClient) -> None:
    resp = client.post(f"/api/v1/jobs/{uuid4()}/analyze")
    assert resp.status_code == 404
