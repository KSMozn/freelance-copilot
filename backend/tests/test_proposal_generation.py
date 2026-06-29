from uuid import uuid4

import pytest

from app.application.services.job_analysis_service import JobAnalysisService
from app.application.services.portfolio_matching_service import (
    PortfolioMatchingService,
)
from app.application.services.portfolio_service import PortfolioService
from app.application.services.proposal_generation_service import (
    ProposalGenerationFailedError,
    ProposalGenerationService,
)
from app.application.services.proposal_review_service import ProposalReviewService
from app.application.services.resume_recommendation_service import (
    ResumeRecommendationService,
)
from app.application.services.resume_service import ResumeService
from app.application.services.scoring_service import ScoringService
from app.domain.exceptions import NotFoundError
from app.domain.profiles.freelancer_profile import DEFAULT_FREELANCER_PROFILE
from app.domain.providers.ai_provider import AIRawResponse
from app.infrastructure.ai.errors import AIProviderResponseError
from app.infrastructure.ai.mock_embedding_provider import MockEmbeddingProvider
from app.infrastructure.ai.mock_provider import MockAIProvider
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


async def _setup(*, with_analysis: bool = True, ai_provider=None):  # type: ignore[no-untyped-def]
    user_id = uuid4()
    portfolios = [
        make_portfolio(
            user_id=user_id,
            title="AI Document Q&A — Arabic RAG Platform",
            business_domain="Document Management",
            technologies=["FastAPI", "Python", "PostgreSQL", "pgvector", "RAG"],
            skills=["FastAPI", "RAG", "PostgreSQL"],
        ),
    ]
    resumes = [
        make_resume(
            user_id=user_id,
            title="AI / LLM Platform Resume",
            primary_skills=["Python", "FastAPI", "RAG", "OpenAI"],
            domains=["AI SaaS"],
        ),
    ]
    job = make_job(
        user_id=user_id,
        title="FastAPI + PostgreSQL backend with RAG over PDFs",
        description=(
            "Need Python FastAPI PostgreSQL Docker RAG over PDFs for an AI SaaS. "
            "OpenAI. Long term. Senior engineer."
        ),
        proposal_count=8,
    )

    job_repo = FakeJobRepository([job])
    portfolio_repo = FakePortfolioRepository(portfolios)
    resume_repo = FakeResumeRepository(resumes)
    analysis_repo = FakeAnalysisRepository()
    score_repo = FakeScoreRepository()
    embedding_repo = FakeEmbeddingRepository()
    proposal_repo = FakeProposalRepository()
    embedding_provider = MockEmbeddingProvider()

    portfolio_service = PortfolioService(
        portfolio_repo=portfolio_repo,
        embedding_repo=embedding_repo,
        embedding_provider=embedding_provider,
    )
    for p in portfolios:
        await portfolio_service.ensure_embedding(p)
    resume_service = ResumeService(
        resume_repo=resume_repo,
        embedding_repo=embedding_repo,
        embedding_provider=embedding_provider,
    )
    for r in resumes:
        await resume_service.ensure_embedding(r)

    if with_analysis:
        analyzer = JobAnalysisService(
            job_repo=job_repo,
            analysis_repo=analysis_repo,
            score_repo=score_repo,
            ai_provider=MockAIProvider(),
            scoring=ScoringService(DEFAULT_FREELANCER_PROFILE),
        )
        await analyzer.analyze(user_id=user_id, job_id=job.id)

    matching = PortfolioMatchingService(
        job_repo=job_repo,
        portfolio_repo=portfolio_repo,
        analysis_repo=analysis_repo,
        embedding_repo=embedding_repo,
        portfolio_service=portfolio_service,
        embedding_provider=embedding_provider,
        profile=DEFAULT_FREELANCER_PROFILE,
    )
    recs = ResumeRecommendationService(
        job_repo=job_repo,
        resume_repo=resume_repo,
        analysis_repo=analysis_repo,
        embedding_repo=embedding_repo,
        resume_service=resume_service,
        embedding_provider=embedding_provider,
    )
    gen = ProposalGenerationService(
        job_repo=job_repo,
        analysis_repo=analysis_repo,
        score_repo=score_repo,
        portfolio_repo=portfolio_repo,
        portfolio_matching_service=matching,
        resume_recommendation_service=recs,
        proposal_repo=proposal_repo,
        ai_provider=ai_provider or MockAIProvider(),
        review_service=ProposalReviewService(),
    )
    return user_id, job, gen, proposal_repo


async def test_generation_requires_analysis() -> None:
    user_id, job, gen, _ = await _setup(with_analysis=False)
    with pytest.raises(NotFoundError):
        await gen.generate(user_id=user_id, job_id=job.id)


async def test_generation_persists_proposal_with_quality_score() -> None:
    user_id, job, gen, proposal_repo = await _setup()
    result = await gen.generate(user_id=user_id, job_id=job.id)

    assert result.body
    assert result.title
    assert result.quality_score is not None
    assert 0 <= result.quality_score <= 100
    assert result.quality_breakdown is not None
    # the persisted row carries the same score
    persisted = await proposal_repo.get_by_id(result.id, user_id=user_id)
    assert persisted is not None
    assert persisted.quality_score == result.quality_score


async def test_generation_records_used_portfolio_and_resume_ids() -> None:
    user_id, job, gen, _ = await _setup()
    result = await gen.generate(user_id=user_id, job_id=job.id)
    assert result.portfolio_ids, "expected at least one portfolio_id recorded"
    assert result.resume_id is not None


async def test_invalid_provider_payload_raises() -> None:
    class _BadProvider:
        name = "bad"
        model = "bad"

        async def complete_json(self, *, system_prompt: str, user_prompt: str):
            return AIRawResponse(data={"title": ""}, provider=self.name, model=self.model)

    user_id, job, gen, _ = await _setup(ai_provider=_BadProvider())
    with pytest.raises(ProposalGenerationFailedError):
        await gen.generate(user_id=user_id, job_id=job.id)


async def test_provider_http_error_raises() -> None:
    class _ExplodingProvider:
        name = "exploding"
        model = "exploding"

        async def complete_json(self, *, system_prompt: str, user_prompt: str):
            raise AIProviderResponseError("500")

    user_id, job, gen, _ = await _setup(ai_provider=_ExplodingProvider())
    with pytest.raises(ProposalGenerationFailedError):
        await gen.generate(user_id=user_id, job_id=job.id)


async def test_update_and_re_review_recomputes_score() -> None:
    user_id, job, gen, _ = await _setup()
    first = await gen.generate(user_id=user_id, job_id=job.id)
    # User edits body to something obviously generic — re-review must dock score.
    edited = await gen.update(
        user_id=user_id,
        proposal_id=first.id,
        fields={
            "body": (
                "I am excited to apply for this project. I am a perfect fit. "
                "I have extensive experience and I can help you with this project."
            )
        },
    )
    assert edited.body.startswith("I am excited")
    re_reviewed = await gen.re_review(user_id=user_id, proposal_id=first.id)
    assert re_reviewed.quality_score is not None
    assert re_reviewed.quality_score < (first.quality_score or 100)


async def test_get_latest_returns_most_recent() -> None:
    user_id, job, gen, _ = await _setup()
    p1 = await gen.generate(user_id=user_id, job_id=job.id)
    p2 = await gen.generate(user_id=user_id, job_id=job.id)
    latest = await gen.get_latest_for_job(user_id=user_id, job_id=job.id)
    assert latest is not None
    assert latest.id in (p1.id, p2.id)
    # The list is ordered by created_at desc
    all_props = await gen.list_for_job(user_id=user_id, job_id=job.id)
    assert all_props[0].id == latest.id


async def test_delete_proposal() -> None:
    user_id, job, gen, _ = await _setup()
    proposal = await gen.generate(user_id=user_id, job_id=job.id)
    await gen.delete(user_id=user_id, proposal_id=proposal.id)
    with pytest.raises(NotFoundError):
        await gen.get(user_id=user_id, proposal_id=proposal.id)
