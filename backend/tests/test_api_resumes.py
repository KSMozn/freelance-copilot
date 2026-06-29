"""API tests for the Phase-4 endpoints — fakes only, no DB needed."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.services.job_analysis_service import JobAnalysisService
from app.application.services.resume_recommendation_service import (
    ResumeRecommendationService,
)
from app.application.services.resume_service import ResumeService
from app.application.services.scoring_service import ScoringService
from app.core.deps import (
    get_current_user,
    get_job_analysis_service,
    get_resume_recommendation_service,
    get_resume_service,
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
    FakeResumeRepository,
    FakeScoreRepository,
    make_job,
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
    resumes = FakeResumeRepository(
        [
            make_resume(
                user_id=user.id,
                title="AI / LLM Platform Resume",
                primary_skills=["Python", "FastAPI", "RAG", "OpenAI"],
                domains=["AI SaaS"],
            ),
            make_resume(
                user_id=user.id,
                title="Engineering Manager Resume",
                primary_skills=["Engineering strategy", "Mentoring"],
                domains=["Enterprise SaaS"],
                seniority_level="lead",
            ),
        ]
    )
    job = make_job(
        user_id=user.id,
        title="FastAPI RAG backend",
        description="Need FastAPI PostgreSQL pgvector RAG over PDFs. AI SaaS. Python Docker.",
        proposal_count=8,
    )
    jobs = FakeJobRepository([job])
    return {
        "resumes": resumes,
        "jobs": jobs,
        "analysis_repo": FakeAnalysisRepository(),
        "score_repo": FakeScoreRepository(),
        "embeddings": FakeEmbeddingRepository(),
        "embedding_provider": MockEmbeddingProvider(),
        "job": job,
    }


@pytest.fixture
def client(user: User, state):  # type: ignore[no-untyped-def]
    def _resume_service() -> ResumeService:
        return ResumeService(
            resume_repo=state["resumes"],
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

    def _rec_service() -> ResumeRecommendationService:
        return ResumeRecommendationService(
            job_repo=state["jobs"],
            resume_repo=state["resumes"],
            analysis_repo=state["analysis_repo"],
            embedding_repo=state["embeddings"],
            resume_service=_resume_service(),
            embedding_provider=state["embedding_provider"],
        )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_resume_service] = _resume_service
    app.dependency_overrides[get_job_analysis_service] = _analysis_service
    app.dependency_overrides[get_resume_recommendation_service] = _rec_service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# auth gating
def test_resume_list_requires_auth() -> None:
    with TestClient(app) as raw:
        assert raw.get("/api/v1/resumes").status_code == 401


def test_resume_create_requires_auth() -> None:
    with TestClient(app) as raw:
        assert raw.post("/api/v1/resumes", json={}).status_code == 401


def test_recommend_requires_auth(state) -> None:  # type: ignore[no-untyped-def]
    with TestClient(app) as raw:
        assert (
            raw.post(f"/api/v1/jobs/{state['job'].id}/recommend-resume").status_code == 401
        )


# CRUD happy paths
def test_create_get_update_delete_cycle(client: TestClient) -> None:
    payload = {
        "title": "New Resume",
        "target_role": "Engineer",
        "summary": "An engineer.",
        "seniority_level": "senior",
        "primary_skills": ["Python", "FastAPI"],
        "secondary_skills": ["Docker"],
        "industries": ["AI SaaS"],
        "domains": ["AI SaaS"],
        "achievements": [],
        "project_highlights": [],
        "keywords": [],
        "notes": None,
    }
    created = client.post("/api/v1/resumes", json=payload)
    assert created.status_code == 201, created.text
    body = created.json()
    rid = body["id"]
    assert body["title"] == "New Resume"
    assert body["primary_skills"] == ["Python", "FastAPI"]

    got = client.get(f"/api/v1/resumes/{rid}")
    assert got.status_code == 200

    upd = client.put(
        f"/api/v1/resumes/{rid}", json={"title": "New Resume v2"}
    )
    assert upd.status_code == 200
    assert upd.json()["title"] == "New Resume v2"

    deleted = client.delete(f"/api/v1/resumes/{rid}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/resumes/{rid}").status_code == 404


def test_list_returns_seeded_resumes(client: TestClient) -> None:
    listing = client.get("/api/v1/resumes").json()
    assert listing["total"] == 2


# Recommendation
def test_recommend_404_before_analysis(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    assert (
        client.post(f"/api/v1/jobs/{state['job'].id}/recommend-resume").status_code == 404
    )


def test_recommend_after_analyze_ranks_results(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    job_id = state["job"].id
    r = client.post(f"/api/v1/jobs/{job_id}/analyze")
    assert r.status_code == 200, r.text

    recs = client.post(f"/api/v1/jobs/{job_id}/recommend-resume")
    assert recs.status_code == 200, recs.text
    body = recs.json()
    assert body["job_id"] == str(job_id)
    assert body["resume_count"] == 2
    assert len(body["recommendations"]) == 2

    top = body["recommendations"][0]
    assert "AI / LLM" in top["title"]
    assert 0.0 <= top["match_score"] <= 1.0
    assert top["fit_reasons"]


def test_get_endpoint_returns_same_ranking(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    job_id = state["job"].id
    client.post(f"/api/v1/jobs/{job_id}/analyze")
    via_post = client.post(f"/api/v1/jobs/{job_id}/recommend-resume").json()
    via_get = client.get(f"/api/v1/jobs/{job_id}/resume-recommendations").json()
    assert (
        via_post["recommendations"][0]["resume_id"]
        == via_get["recommendations"][0]["resume_id"]
    )


def test_top_n_caps_results(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    job_id = state["job"].id
    client.post(f"/api/v1/jobs/{job_id}/analyze")
    body = client.post(f"/api/v1/jobs/{job_id}/recommend-resume?top_n=1").json()
    assert len(body["recommendations"]) == 1
