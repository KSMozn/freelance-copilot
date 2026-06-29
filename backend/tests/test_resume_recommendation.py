from uuid import uuid4

import pytest

from app.application.services.job_analysis_service import JobAnalysisService
from app.application.services.resume_recommendation_service import (
    ResumeRecommendationService,
    hybrid_score,
)
from app.application.services.resume_service import ResumeService
from app.application.services.scoring_service import ScoringService
from app.domain.exceptions import NotFoundError
from app.domain.profiles.freelancer_profile import DEFAULT_FREELANCER_PROFILE
from app.infrastructure.ai.mock_embedding_provider import MockEmbeddingProvider
from app.infrastructure.ai.mock_provider import MockAIProvider
from tests.factories import (
    FakeAnalysisRepository,
    FakeEmbeddingRepository,
    FakeJobRepository,
    FakeResumeRepository,
    FakeScoreRepository,
    make_job,
    make_resume,
)


async def _seed_analyzed_job(*, user_id, resumes):  # type: ignore[no-untyped-def]
    job = make_job(
        user_id=user_id,
        title="FastAPI + PostgreSQL backend with RAG over PDFs",
        description=(
            "Need Python, FastAPI, PostgreSQL, Docker, RAG over PDFs. AI SaaS. "
            "Pgvector and OpenAI. Senior engineer."
        ),
        proposal_count=10,
    )
    job_repo = FakeJobRepository([job])
    resume_repo = FakeResumeRepository(resumes)
    analysis_repo = FakeAnalysisRepository()
    score_repo = FakeScoreRepository()
    embedding_repo = FakeEmbeddingRepository()
    embedding_provider = MockEmbeddingProvider()

    resume_service = ResumeService(
        resume_repo=resume_repo,
        embedding_repo=embedding_repo,
        embedding_provider=embedding_provider,
    )
    for r in resumes:
        await resume_service.ensure_embedding(r)

    analysis_service = JobAnalysisService(
        job_repo=job_repo,
        analysis_repo=analysis_repo,
        score_repo=score_repo,
        ai_provider=MockAIProvider(),
        scoring=ScoringService(DEFAULT_FREELANCER_PROFILE),
    )
    await analysis_service.analyze(user_id=user_id, job_id=job.id)

    rec_service = ResumeRecommendationService(
        job_repo=job_repo,
        resume_repo=resume_repo,
        analysis_repo=analysis_repo,
        embedding_repo=embedding_repo,
        resume_service=resume_service,
        embedding_provider=embedding_provider,
    )
    return rec_service, job


async def test_recommend_requires_existing_analysis() -> None:
    user_id = uuid4()
    job = make_job(user_id=user_id)
    job_repo = FakeJobRepository([job])
    resumes = FakeResumeRepository()
    analysis_repo = FakeAnalysisRepository()
    embedding_repo = FakeEmbeddingRepository()
    provider = MockEmbeddingProvider()
    resume_service = ResumeService(
        resume_repo=resumes, embedding_repo=embedding_repo, embedding_provider=provider
    )
    rec = ResumeRecommendationService(
        job_repo=job_repo,
        resume_repo=resumes,
        analysis_repo=analysis_repo,
        embedding_repo=embedding_repo,
        resume_service=resume_service,
        embedding_provider=provider,
    )
    with pytest.raises(NotFoundError):
        await rec.recommend(user_id=user_id, job_id=job.id)


async def test_recommend_with_no_resumes_returns_empty() -> None:
    user_id = uuid4()
    rec, job = await _seed_analyzed_job(user_id=user_id, resumes=[])
    result = await rec.recommend(user_id=user_id, job_id=job.id)
    assert result.recommendations == []
    assert result.resume_count == 0


async def test_strong_resume_outranks_weak_one() -> None:
    user_id = uuid4()
    strong = make_resume(
        user_id=user_id,
        title="AI / LLM Platform Resume",
        target_role="AI / Backend Engineer",
        seniority_level="senior",
        primary_skills=["Python", "FastAPI", "RAG", "OpenAI", "PostgreSQL"],
        secondary_skills=["Docker", "Claude"],
        domains=["AI SaaS"],
        achievements=["Shipped a production RAG platform."],
        project_highlights=["On-prem RAG over enterprise docs."],
        keywords=["RAG", "LLM"],
        summary="RAG + FastAPI + PostgreSQL backend engineer.",
    )
    weak = make_resume(
        user_id=user_id,
        title="Engineering Manager Resume",
        target_role="Engineering Manager",
        seniority_level="lead",
        primary_skills=["Engineering strategy", "Mentoring"],
        secondary_skills=["Hiring"],
        domains=["Enterprise SaaS"],
        achievements=["Led a distributed platform team."],
        project_highlights=["Stood up a platform team."],
        keywords=["engineering manager"],
        summary="Player-coach EM.",
    )
    rec, job = await _seed_analyzed_job(user_id=user_id, resumes=[strong, weak])
    result = await rec.recommend(user_id=user_id, job_id=job.id)

    assert len(result.recommendations) == 2
    top, bottom = result.recommendations
    assert top.title == strong.title
    assert top.match_score > bottom.match_score
    assert top.fit_reasons
    assert top.relevant_skills


async def test_missing_skills_called_out() -> None:
    user_id = uuid4()
    sparse = make_resume(
        user_id=user_id,
        title="Sparse Resume",
        primary_skills=["Python"],
        secondary_skills=[],
        domains=[],
    )
    rec, job = await _seed_analyzed_job(user_id=user_id, resumes=[sparse])
    result = await rec.recommend(user_id=user_id, job_id=job.id)
    top = result.recommendations[0]
    # The job requires more than just Python — expect some gaps to surface.
    assert top.missing_or_weak_skills


async def test_hybrid_score_weights_sum_to_one() -> None:
    s = hybrid_score(semantic=1.0, skill=1.0, domain=1.0, seniority=1.0)
    assert abs(s - 1.0) < 1e-9
    s2 = hybrid_score(semantic=1.0, skill=0.0, domain=0.0, seniority=0.0)
    assert abs(s2 - 0.55) < 1e-9
    s3 = hybrid_score(semantic=0.0, skill=1.0, domain=0.0, seniority=0.0)
    assert abs(s3 - 0.30) < 1e-9
    s4 = hybrid_score(semantic=0.0, skill=0.0, domain=1.0, seniority=0.0)
    assert abs(s4 - 0.10) < 1e-9
    s5 = hybrid_score(semantic=0.0, skill=0.0, domain=0.0, seniority=1.0)
    assert abs(s5 - 0.05) < 1e-9


async def test_top_n_caps_results() -> None:
    user_id = uuid4()
    resumes = [
        make_resume(user_id=user_id, title=f"Resume {i}", primary_skills=["Python"])
        for i in range(5)
    ]
    rec, job = await _seed_analyzed_job(user_id=user_id, resumes=resumes)
    result = await rec.recommend(user_id=user_id, job_id=job.id, top_n=2)
    assert len(result.recommendations) == 2
    assert result.resume_count == 5
