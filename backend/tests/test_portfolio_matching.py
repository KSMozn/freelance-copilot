from uuid import uuid4

import pytest

from app.application.services.job_analysis_service import JobAnalysisService
from app.application.services.portfolio_matching_service import (
    PortfolioMatchingService,
    hybrid_score,
)
from app.application.services.portfolio_service import PortfolioService
from app.application.services.scoring_service import ScoringService
from app.domain.exceptions import NotFoundError
from app.domain.profiles.freelancer_profile import DEFAULT_FREELANCER_PROFILE
from app.infrastructure.ai.mock_embedding_provider import MockEmbeddingProvider
from app.infrastructure.ai.mock_provider import MockAIProvider
from tests.factories import (
    FakeAnalysisRepository,
    FakeEmbeddingRepository,
    FakeJobRepository,
    FakePortfolioRepository,
    FakeScoreRepository,
    make_job,
    make_portfolio,
)


async def _seed_analyzed_job(*, user_id, portfolios):  # type: ignore[no-untyped-def]
    """Wire up the same object graph the API would for one user + job + portfolios."""
    job = make_job(
        user_id=user_id,
        title="FastAPI + PostgreSQL backend with RAG over PDFs",
        description=(
            "Need Python FastAPI PostgreSQL Docker RAG over PDFs for an AI SaaS. "
            "Long term collaboration. Pgvector and OpenAI."
        ),
        proposal_count=10,
    )
    job_repo = FakeJobRepository([job])
    portfolio_repo = FakePortfolioRepository(portfolios)
    analysis_repo = FakeAnalysisRepository()
    score_repo = FakeScoreRepository()
    embedding_repo = FakeEmbeddingRepository()
    embedding_provider = MockEmbeddingProvider()

    portfolio_service = PortfolioService(
        portfolio_repo=portfolio_repo,
        embedding_repo=embedding_repo,
        embedding_provider=embedding_provider,
    )
    # seed portfolio embeddings
    for p in portfolios:
        await portfolio_service.ensure_embedding(p)

    # run analysis so the matching service finds it
    analysis_service = JobAnalysisService(
        job_repo=job_repo,
        analysis_repo=analysis_repo,
        score_repo=score_repo,
        ai_provider=MockAIProvider(),
        scoring=ScoringService(DEFAULT_FREELANCER_PROFILE),
    )
    await analysis_service.analyze(user_id=user_id, job_id=job.id)

    matching = PortfolioMatchingService(
        job_repo=job_repo,
        portfolio_repo=portfolio_repo,
        analysis_repo=analysis_repo,
        embedding_repo=embedding_repo,
        portfolio_service=portfolio_service,
        embedding_provider=embedding_provider,
        profile=DEFAULT_FREELANCER_PROFILE,
    )
    return matching, job, analysis_service


async def test_match_returns_404_without_analysis() -> None:
    user_id = uuid4()
    job = make_job(user_id=user_id)
    job_repo = FakeJobRepository([job])
    portfolios = FakePortfolioRepository()
    analysis_repo = FakeAnalysisRepository()
    embedding_repo = FakeEmbeddingRepository()
    provider = MockEmbeddingProvider()
    portfolio_service = PortfolioService(
        portfolio_repo=portfolios,
        embedding_repo=embedding_repo,
        embedding_provider=provider,
    )
    matching = PortfolioMatchingService(
        job_repo=job_repo,
        portfolio_repo=portfolios,
        analysis_repo=analysis_repo,
        embedding_repo=embedding_repo,
        portfolio_service=portfolio_service,
        embedding_provider=provider,
        profile=DEFAULT_FREELANCER_PROFILE,
    )
    with pytest.raises(NotFoundError):
        await matching.match(user_id=user_id, job_id=job.id)


async def test_match_with_no_portfolios_returns_empty_list() -> None:
    user_id = uuid4()
    matching, job, _ = await _seed_analyzed_job(user_id=user_id, portfolios=[])
    result = await matching.match(user_id=user_id, job_id=job.id)
    assert result.matches == []
    assert result.portfolio_count == 0


async def test_strong_portfolio_outranks_weak_one() -> None:
    user_id = uuid4()
    strong = make_portfolio(
        user_id=user_id,
        title="AI Document Q&A — Arabic RAG Platform",
        business_domain="Document Management",
        technologies=[
            "FastAPI",
            "Python",
            "PostgreSQL",
            "pgvector",
            "OpenAI",
            "Docker",
            "RAG",
            "LLM",
        ],
        skills=["FastAPI", "RAG", "LLM", "PostgreSQL", "Docker"],
        long_description=(
            "On-prem RAG platform with FastAPI, PostgreSQL, pgvector, OpenAI, "
            "Docker; AI SaaS scenarios; long-term."
        ),
    )
    weak = make_portfolio(
        user_id=user_id,
        title="Vintage furniture restoration site",
        business_domain="Retail",
        technologies=["WordPress", "PHP", "MySQL"],
        skills=["WordPress", "CMS"],
        long_description="Static WordPress site for furniture restoration.",
    )

    matching, job, _ = await _seed_analyzed_job(user_id=user_id, portfolios=[strong, weak])
    result = await matching.match(user_id=user_id, job_id=job.id)

    assert len(result.matches) == 2
    top = result.matches[0]
    bottom = result.matches[1]
    assert top.title == strong.title
    assert top.match_score > bottom.match_score
    # the top match must come with at least one human-readable reason
    assert top.match_reasons
    # skill_overlap should pick up at least one of FastAPI/PostgreSQL/RAG
    assert any(
        s.lower() in {"fastapi", "postgresql", "rag", "openai"} for s in top.relevant_skills
    )


async def test_match_score_components_compose_correctly() -> None:
    """Sanity-check that the hybrid_score helper applies the documented weights."""
    s = hybrid_score(semantic=1.0, skill=1.0, domain=1.0, strategic=1.0)
    assert abs(s - 1.0) < 1e-9
    s2 = hybrid_score(semantic=1.0, skill=0.0, domain=0.0, strategic=0.0)
    assert abs(s2 - 0.6) < 1e-9
    s3 = hybrid_score(semantic=0.0, skill=1.0, domain=0.0, strategic=0.0)
    assert abs(s3 - 0.25) < 1e-9


async def test_top_n_caps_results() -> None:
    user_id = uuid4()
    portfolios = [
        make_portfolio(user_id=user_id, title=f"P{i}", technologies=["Python"], skills=["Python"])
        for i in range(7)
    ]
    matching, job, _ = await _seed_analyzed_job(user_id=user_id, portfolios=portfolios)
    result = await matching.match(user_id=user_id, job_id=job.id, top_n=3)
    assert len(result.matches) == 3
    assert result.portfolio_count == 7
