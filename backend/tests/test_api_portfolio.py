"""API-level tests for Phase 3.

Uses dependency overrides + in-memory fakes so no Postgres is required.
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.services.job_analysis_service import JobAnalysisService
from app.application.services.portfolio_matching_service import PortfolioMatchingService
from app.application.services.portfolio_service import PortfolioService
from app.application.services.scoring_service import ScoringService
from app.core.deps import (
    get_current_user,
    get_job_analysis_service,
    get_portfolio_matching_service,
    get_portfolio_service,
)
from app.domain.entities.user import User
from app.domain.profiles.freelancer_profile import DEFAULT_FREELANCER_PROFILE
from app.infrastructure.ai.mock_embedding_provider import MockEmbeddingProvider
from app.infrastructure.ai.mock_provider import MockAIProvider
from app.main import app
from tests.factories import (
    FakeAnalysisRepository,
    FakeEmbeddingRepository,
    FakeJobRepository,
    FakePortfolioRepository,
    FakeScoreRepository,
    make_job,
    make_portfolio,
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
def state(user: User):  # type: ignore[no-untyped-def]
    """Shared fake stores so matching + portfolio + analysis services see the same world."""
    portfolios = FakePortfolioRepository(
        [
            make_portfolio(
                user_id=user.id,
                title="AI Document Q&A — Arabic RAG Platform",
                business_domain="Document Management",
                technologies=["FastAPI", "Python", "PostgreSQL", "pgvector", "RAG"],
                skills=["FastAPI", "RAG", "PostgreSQL"],
            ),
            make_portfolio(
                user_id=user.id,
                title="Vintage furniture site",
                business_domain="Retail",
                technologies=["WordPress"],
                skills=["WordPress"],
            ),
        ]
    )
    job = make_job(
        user_id=user.id,
        title="FastAPI RAG backend",
        description=(
            "Need FastAPI PostgreSQL pgvector RAG over PDFs. AI SaaS. Python Docker."
        ),
        proposal_count=8,
    )
    jobs = FakeJobRepository([job])
    analysis_repo = FakeAnalysisRepository()
    score_repo = FakeScoreRepository()
    embeddings = FakeEmbeddingRepository()
    embedding_provider = MockEmbeddingProvider()

    return {
        "portfolios": portfolios,
        "jobs": jobs,
        "analysis_repo": analysis_repo,
        "score_repo": score_repo,
        "embeddings": embeddings,
        "embedding_provider": embedding_provider,
        "job": job,
    }


@pytest.fixture
def client(user: User, state):  # type: ignore[no-untyped-def]
    def _portfolio_service() -> PortfolioService:
        return PortfolioService(
            portfolio_repo=state["portfolios"],
            embedding_repo=state["embeddings"],
            embedding_provider=state["embedding_provider"],
        )

    def _analysis_service() -> JobAnalysisService:
        return JobAnalysisService(
            job_repo=state["jobs"],
            analysis_repo=state["analysis_repo"],
            score_repo=state["score_repo"],
            ai_provider=MockAIProvider(),
            scoring=ScoringService(DEFAULT_FREELANCER_PROFILE),
        )

    def _matching_service() -> PortfolioMatchingService:
        return PortfolioMatchingService(
            job_repo=state["jobs"],
            portfolio_repo=state["portfolios"],
            analysis_repo=state["analysis_repo"],
            embedding_repo=state["embeddings"],
            portfolio_service=_portfolio_service(),
            embedding_provider=state["embedding_provider"],
            profile=DEFAULT_FREELANCER_PROFILE,
        )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_portfolio_service] = _portfolio_service
    app.dependency_overrides[get_job_analysis_service] = _analysis_service
    app.dependency_overrides[get_portfolio_matching_service] = _matching_service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# ---- auth gating ----

def test_portfolio_list_requires_auth() -> None:
    with TestClient(app) as raw:
        assert raw.get("/api/v1/portfolio").status_code == 401


def test_portfolio_create_requires_auth() -> None:
    with TestClient(app) as raw:
        assert raw.post("/api/v1/portfolio", json={}).status_code == 401


def test_match_requires_auth(state) -> None:  # type: ignore[no-untyped-def]
    with TestClient(app) as raw:
        assert raw.post(f"/api/v1/jobs/{state['job'].id}/match-portfolio").status_code == 401


# ---- crud ----

def test_create_and_list_portfolio(client: TestClient) -> None:
    payload = {
        "title": "New Project",
        "long_description": "Built X with Y and Z.",
        "short_description": "Built X with Y and Z.",
        "role": "Engineer",
        "business_domain": "AI SaaS",
        "technologies": ["Python", "FastAPI"],
        "skills": ["Python"],
        "features": [],
        "outcomes": [],
        "highlight": False,
    }
    resp = client.post("/api/v1/portfolio", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "New Project"
    assert body["technologies"] == ["Python", "FastAPI"]

    listing = client.get("/api/v1/portfolio").json()
    assert listing["total"] >= 1
    assert any(p["title"] == "New Project" for p in listing["items"])


def test_get_and_delete_portfolio(client: TestClient) -> None:
    created = client.post(
        "/api/v1/portfolio",
        json={
            "title": "Throwaway",
            "long_description": "x",
            "technologies": [],
            "skills": [],
        },
    ).json()
    pid = created["id"]

    got = client.get(f"/api/v1/portfolio/{pid}")
    assert got.status_code == 200
    assert got.json()["id"] == pid

    deleted = client.delete(f"/api/v1/portfolio/{pid}")
    assert deleted.status_code == 204

    after = client.get(f"/api/v1/portfolio/{pid}")
    assert after.status_code == 404


# ---- matching ----

def test_match_returns_404_before_analysis(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(f"/api/v1/jobs/{state['job'].id}/match-portfolio")
    assert resp.status_code == 404


def test_match_after_analyze_returns_ranked_results(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    job_id = state["job"].id
    # run analysis first
    r = client.post(f"/api/v1/jobs/{job_id}/analyze")
    assert r.status_code == 200, r.text

    matches = client.post(f"/api/v1/jobs/{job_id}/match-portfolio")
    assert matches.status_code == 200, matches.text
    body = matches.json()
    assert body["job_id"] == str(job_id)
    assert body["portfolio_count"] == 2
    assert len(body["matches"]) == 2

    # top match should be the RAG portfolio
    top = body["matches"][0]
    assert "RAG" in top["title"] or "Document" in top["title"]
    assert 0.0 <= top["match_score"] <= 1.0
    # explanation fields are populated
    assert top["match_reasons"]


def test_get_endpoint_matches_post_endpoint(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    job_id = state["job"].id
    client.post(f"/api/v1/jobs/{job_id}/analyze")
    via_post = client.post(f"/api/v1/jobs/{job_id}/match-portfolio").json()
    via_get = client.get(f"/api/v1/jobs/{job_id}/portfolio-matches").json()
    # ranking is deterministic over the same input — top match must agree
    assert via_post["matches"][0]["portfolio_id"] == via_get["matches"][0]["portfolio_id"]


def test_top_n_query_param_caps_results(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    job_id = state["job"].id
    client.post(f"/api/v1/jobs/{job_id}/analyze")
    resp = client.post(f"/api/v1/jobs/{job_id}/match-portfolio?top_n=1").json()
    assert len(resp["matches"]) == 1
