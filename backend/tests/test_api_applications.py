"""API-level Phase-6 tests using dependency overrides only (no DB)."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.services.application_service import ApplicationService
from app.application.services.job_analysis_service import JobAnalysisService
from app.application.services.portfolio_matching_service import (
    PortfolioMatchingService,
)
from app.application.services.portfolio_service import PortfolioService
from app.application.services.proposal_generation_service import (
    ProposalGenerationService,
)
from app.application.services.proposal_review_service import ProposalReviewService
from app.application.services.resume_recommendation_service import (
    ResumeRecommendationService,
)
from app.application.services.resume_service import ResumeService
from app.application.services.scoring_service import ScoringService
from app.core.deps import (
    get_application_service,
    get_current_user,
    get_job_analysis_service,
    get_proposal_generation_service,
)
from app.domain.entities.user import User
from app.domain.profiles.freelancer_profile import DEFAULT_FREELANCER_PROFILE
from app.infrastructure.ai.mock_embedding_provider import MockEmbeddingProvider
from app.infrastructure.ai.mock_provider import MockAIProvider
from app.main import app
from tests.factories import (
    FakeAnalysisRepository,
    FakeApplicationHistoryRepository,
    FakeApplicationRepository,
    FakeEmbeddingRepository,
    FakeJobRepository,
    FakePortfolioRepository,
    FakeProposalRepository,
    FakeResumeRepository,
    FakeScoreRepository,
    make_job,
    make_portfolio,
    make_resume,
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
    portfolios = FakePortfolioRepository(
        [
            make_portfolio(
                user_id=user.id,
                title="AI Document Q&A — Arabic RAG Platform",
                business_domain="Document Management",
                technologies=["FastAPI", "Python", "PostgreSQL", "pgvector", "RAG"],
                skills=["FastAPI", "RAG", "PostgreSQL"],
            ),
        ]
    )
    resumes = FakeResumeRepository(
        [
            make_resume(
                user_id=user.id,
                title="AI / LLM Platform Resume",
                primary_skills=["Python", "FastAPI", "RAG"],
                domains=["AI SaaS"],
            ),
        ]
    )
    job = make_job(
        user_id=user.id,
        title="FastAPI RAG backend",
        description="Need FastAPI PostgreSQL pgvector RAG over PDFs. AI SaaS. Python Docker. OpenAI.",
        proposal_count=8,
    )
    return {
        "jobs": FakeJobRepository([job]),
        "portfolios": portfolios,
        "resumes": resumes,
        "analysis_repo": FakeAnalysisRepository(),
        "score_repo": FakeScoreRepository(),
        "embeddings": FakeEmbeddingRepository(),
        "proposals": FakeProposalRepository(),
        "applications": FakeApplicationRepository(),
        "history": FakeApplicationHistoryRepository(),
        "embedding_provider": MockEmbeddingProvider(),
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

    def _resume_service() -> ResumeService:
        return ResumeService(
            resume_repo=state["resumes"],
            embedding_repo=state["embeddings"],
            embedding_provider=state["embedding_provider"],
        )

    def _matching() -> PortfolioMatchingService:
        return PortfolioMatchingService(
            job_repo=state["jobs"],
            portfolio_repo=state["portfolios"],
            analysis_repo=state["analysis_repo"],
            embedding_repo=state["embeddings"],
            portfolio_service=_portfolio_service(),
            embedding_provider=state["embedding_provider"],
            profile=DEFAULT_FREELANCER_PROFILE,
        )

    def _recs() -> ResumeRecommendationService:
        return ResumeRecommendationService(
            job_repo=state["jobs"],
            resume_repo=state["resumes"],
            analysis_repo=state["analysis_repo"],
            embedding_repo=state["embeddings"],
            resume_service=_resume_service(),
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

    def _proposal_service() -> ProposalGenerationService:
        return ProposalGenerationService(
            job_repo=state["jobs"],
            analysis_repo=state["analysis_repo"],
            score_repo=state["score_repo"],
            portfolio_repo=state["portfolios"],
            portfolio_matching_service=_matching(),
            resume_recommendation_service=_recs(),
            proposal_repo=state["proposals"],
            ai_provider=MockAIProvider(),
            review_service=ProposalReviewService(),
        )

    def _application_service() -> ApplicationService:
        return ApplicationService(
            application_repo=state["applications"],
            history_repo=state["history"],
            job_repo=state["jobs"],
            proposal_repo=state["proposals"],
            resume_repo=state["resumes"],
            portfolio_repo=state["portfolios"],
            score_repo=state["score_repo"],
            portfolio_matching_service=_matching(),
            resume_recommendation_service=_recs(),
        )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_job_analysis_service] = _analysis_service
    app.dependency_overrides[get_proposal_generation_service] = _proposal_service
    app.dependency_overrides[get_application_service] = _application_service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _bootstrap_proposal(client: TestClient, job_id) -> str:  # type: ignore[no-untyped-def]
    r1 = client.post(f"/api/v1/jobs/{job_id}/analyze")
    assert r1.status_code == 200, r1.text
    r2 = client.post(f"/api/v1/jobs/{job_id}/proposals/generate")
    assert r2.status_code == 200, r2.text
    return r2.json()["id"]


# ---- auth gating ----

def test_list_requires_auth() -> None:
    with TestClient(app) as raw:
        assert raw.get("/api/v1/applications").status_code == 401


def test_create_from_proposal_requires_auth() -> None:
    with TestClient(app) as raw:
        assert (
            raw.post(f"/api/v1/applications/from-proposal/{uuid4()}").status_code
            == 401
        )


def test_status_patch_requires_auth() -> None:
    with TestClient(app) as raw:
        assert (
            raw.patch(
                f"/api/v1/applications/{uuid4()}/status",
                json={"to_status": "viewed"},
            ).status_code
            == 401
        )


# ---- happy paths ----

def test_create_from_proposal_returns_201_with_snapshot(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    pid = _bootstrap_proposal(client, state["job"].id)
    resp = client.post(f"/api/v1/applications/from-proposal/{pid}")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "applied"
    assert body["applied_at"] is not None
    assert body["snapshot"]["job"]["title"]
    assert body["snapshot"]["proposal"]["body"]


def test_duplicate_active_application_returns_409(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    pid = _bootstrap_proposal(client, state["job"].id)
    first = client.post(f"/api/v1/applications/from-proposal/{pid}")
    assert first.status_code == 201
    second = client.post(f"/api/v1/applications/from-proposal/{pid}")
    assert second.status_code == 409


def test_status_transition_records_history(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    pid = _bootstrap_proposal(client, state["job"].id)
    app_id = client.post(f"/api/v1/applications/from-proposal/{pid}").json()["id"]
    r = client.patch(
        f"/api/v1/applications/{app_id}/status",
        json={"to_status": "viewed", "note": "Got an email"},
    )
    assert r.status_code == 200
    assert r.json()["viewed_at"] is not None
    history = client.get(f"/api/v1/applications/{app_id}/history").json()
    assert len(history) == 2
    assert history[0]["to_status"] == "applied"
    assert history[1]["to_status"] == "viewed"
    assert history[1]["note"] == "Got an email"


def test_invalid_transition_returns_409(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    pid = _bootstrap_proposal(client, state["job"].id)
    app_id = client.post(f"/api/v1/applications/from-proposal/{pid}").json()["id"]
    r = client.patch(
        f"/api/v1/applications/{app_id}/status", json={"to_status": "won"}
    )
    assert r.status_code == 409


def test_details_patch(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    pid = _bootstrap_proposal(client, state["job"].id)
    app_id = client.post(f"/api/v1/applications/from-proposal/{pid}").json()["id"]
    r = client.patch(
        f"/api/v1/applications/{app_id}",
        json={
            "contract_amount": "4500.00",
            "client_response": "Wants a call.",
            "notes": "Calendar link sent.",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["contract_amount"] == "4500.00"
    assert body["client_response"] == "Wants a call."


def test_list_filters_by_status(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    pid = _bootstrap_proposal(client, state["job"].id)
    app_id = client.post(f"/api/v1/applications/from-proposal/{pid}").json()["id"]
    client.patch(
        f"/api/v1/applications/{app_id}/status", json={"to_status": "withdrawn"}
    )
    listing = client.get("/api/v1/applications?status=withdrawn").json()
    assert listing["total"] == 1


def test_delete_application(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    pid = _bootstrap_proposal(client, state["job"].id)
    app_id = client.post(f"/api/v1/applications/from-proposal/{pid}").json()["id"]
    deleted = client.delete(f"/api/v1/applications/{app_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/applications/{app_id}").status_code == 404


def test_unknown_application_returns_404(client: TestClient) -> None:
    assert client.get(f"/api/v1/applications/{uuid4()}").status_code == 404


def test_history_for_unknown_application_returns_404(client: TestClient) -> None:
    assert client.get(f"/api/v1/applications/{uuid4()}/history").status_code == 404
