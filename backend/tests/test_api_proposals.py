"""API-level Phase-5 tests using dependency overrides only (no DB)."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

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
    jobs = FakeJobRepository([job])
    analysis_repo = FakeAnalysisRepository()
    score_repo = FakeScoreRepository()
    embeddings = FakeEmbeddingRepository()
    proposals = FakeProposalRepository()
    return {
        "jobs": jobs,
        "portfolios": portfolios,
        "resumes": resumes,
        "analysis_repo": analysis_repo,
        "score_repo": score_repo,
        "embeddings": embeddings,
        "proposals": proposals,
        "embedding_provider": MockEmbeddingProvider(),
        "job": job,
    }


@pytest.fixture
def client(user: User, state):  # type: ignore[no-untyped-def]
    def _analysis_service() -> JobAnalysisService:
        return JobAnalysisService(
            job_repo=state["jobs"],
            analysis_repo=state["analysis_repo"],
            score_repo=state["score_repo"],
            ai_provider=MockAIProvider(),
            scoring=ScoringService(DEFAULT_FREELANCER_PROFILE),
        )

    def _proposal_service() -> ProposalGenerationService:
        portfolio_service = PortfolioService(
            portfolio_repo=state["portfolios"],
            embedding_repo=state["embeddings"],
            embedding_provider=state["embedding_provider"],
        )
        resume_service = ResumeService(
            resume_repo=state["resumes"],
            embedding_repo=state["embeddings"],
            embedding_provider=state["embedding_provider"],
        )
        matching = PortfolioMatchingService(
            job_repo=state["jobs"],
            portfolio_repo=state["portfolios"],
            analysis_repo=state["analysis_repo"],
            embedding_repo=state["embeddings"],
            portfolio_service=portfolio_service,
            embedding_provider=state["embedding_provider"],
            profile=DEFAULT_FREELANCER_PROFILE,
        )
        recs = ResumeRecommendationService(
            job_repo=state["jobs"],
            resume_repo=state["resumes"],
            analysis_repo=state["analysis_repo"],
            embedding_repo=state["embeddings"],
            resume_service=resume_service,
            embedding_provider=state["embedding_provider"],
        )
        return ProposalGenerationService(
            job_repo=state["jobs"],
            analysis_repo=state["analysis_repo"],
            score_repo=state["score_repo"],
            portfolio_repo=state["portfolios"],
            portfolio_matching_service=matching,
            resume_recommendation_service=recs,
            proposal_repo=state["proposals"],
            ai_provider=MockAIProvider(),
            review_service=ProposalReviewService(),
        )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_job_analysis_service] = _analysis_service
    app.dependency_overrides[get_proposal_generation_service] = _proposal_service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# ---- auth gating ----

def test_generate_requires_auth(state) -> None:  # type: ignore[no-untyped-def]
    with TestClient(app) as raw:
        assert (
            raw.post(f"/api/v1/jobs/{state['job'].id}/proposals/generate").status_code
            == 401
        )


def test_latest_requires_auth(state) -> None:  # type: ignore[no-untyped-def]
    with TestClient(app) as raw:
        assert (
            raw.get(f"/api/v1/jobs/{state['job'].id}/proposals/latest").status_code
            == 401
        )


def test_review_requires_auth() -> None:
    with TestClient(app) as raw:
        assert (
            raw.post(f"/api/v1/proposals/{uuid4()}/review").status_code == 401
        )


# ---- generation path ----

def test_generate_without_analysis_returns_404(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(f"/api/v1/jobs/{state['job'].id}/proposals/generate")
    assert resp.status_code == 404


def test_generate_after_analyze_returns_full_proposal(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    job_id = state["job"].id
    # analyze first
    r = client.post(f"/api/v1/jobs/{job_id}/analyze")
    assert r.status_code == 200, r.text
    gen = client.post(f"/api/v1/jobs/{job_id}/proposals/generate")
    assert gen.status_code == 200, gen.text
    body = gen.json()
    assert body["body"]
    assert body["title"]
    assert body["short_body"]
    assert isinstance(body["questions"], list)
    assert isinstance(body["milestones"], list)
    assert isinstance(body["delivery_approach"], list)
    assert isinstance(body["risk_notes"], list)
    assert 0 <= body["quality_score"] <= 100
    assert sum(body["quality_breakdown"].values()) == body["quality_score"]


def test_latest_and_list_after_generation(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    job_id = state["job"].id
    client.post(f"/api/v1/jobs/{job_id}/analyze")
    client.post(f"/api/v1/jobs/{job_id}/proposals/generate")
    latest = client.get(f"/api/v1/jobs/{job_id}/proposals/latest")
    assert latest.status_code == 200
    listing = client.get(f"/api/v1/jobs/{job_id}/proposals")
    assert listing.status_code == 200
    assert len(listing.json()) >= 1


def test_latest_before_generation_returns_404(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    resp = client.get(f"/api/v1/jobs/{state['job'].id}/proposals/latest")
    assert resp.status_code == 404


def test_update_and_review_cycle(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    job_id = state["job"].id
    client.post(f"/api/v1/jobs/{job_id}/analyze")
    created = client.post(f"/api/v1/jobs/{job_id}/proposals/generate").json()
    pid = created["id"]
    original_score = created["quality_score"]

    upd = client.put(
        f"/api/v1/proposals/{pid}",
        json={
            "body": (
                "I am excited to apply for this project. I am a perfect fit. "
                "I have extensive experience and I can help you with this project."
            )
        },
    )
    assert upd.status_code == 200
    review = client.post(f"/api/v1/proposals/{pid}/review")
    assert review.status_code == 200
    assert review.json()["quality_score"] < original_score
    # Warnings include a banned-phrase entry
    warnings = review.json()["warnings"]
    assert any("Generic phrase detected" in w for w in warnings)


def test_delete_proposal(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    job_id = state["job"].id
    client.post(f"/api/v1/jobs/{job_id}/analyze")
    created = client.post(f"/api/v1/jobs/{job_id}/proposals/generate").json()
    pid = created["id"]

    deleted = client.delete(f"/api/v1/proposals/{pid}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/proposals/{pid}").status_code == 404


def test_unknown_proposal_returns_404(client: TestClient) -> None:
    assert client.get(f"/api/v1/proposals/{uuid4()}").status_code == 404
