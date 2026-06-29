import pytest

from app.application.services.job_analysis_service import (
    AnalysisFailedError,
    JobAnalysisService,
)
from app.application.services.scoring_service import ScoringService
from app.domain.exceptions import NotFoundError
from app.domain.profiles.freelancer_profile import DEFAULT_FREELANCER_PROFILE
from app.domain.providers.ai_provider import AIRawResponse
from app.infrastructure.ai.errors import AIProviderResponseError
from app.infrastructure.ai.mock_provider import MockAIProvider
from tests.factories import (
    FakeAnalysisRepository,
    FakeJobRepository,
    FakeScoreRepository,
    make_job,
)


def _service(provider=None, jobs=None) -> tuple[JobAnalysisService, FakeAnalysisRepository, FakeScoreRepository]:
    analysis_repo = FakeAnalysisRepository()
    score_repo = FakeScoreRepository()
    job_repo = FakeJobRepository(jobs or [])
    service = JobAnalysisService(
        job_repo=job_repo,
        analysis_repo=analysis_repo,
        score_repo=score_repo,
        ai_provider=provider or MockAIProvider(),
        scoring=ScoringService(DEFAULT_FREELANCER_PROFILE),
    )
    return service, analysis_repo, score_repo


async def test_analyze_persists_analysis_and_score() -> None:
    job = make_job(
        title="FastAPI + Postgres RAG",
        description=(
            "Need Python, FastAPI, PostgreSQL, Docker; AI SaaS; long term. "
            "Build RAG over PDFs."
        ),
        proposal_count=6,
    )
    service, analyses, scores = _service(jobs=[job])

    result = await service.analyze(user_id=job.user_id, job_id=job.id)

    assert result.analysis.required_skills
    assert result.score.score >= 50
    assert result.score.recommendation in ("Strong Apply", "Apply", "Maybe", "Skip")
    assert await analyses.get_by_job_id(job.id) is not None
    assert await scores.get_by_job_id(job.id) is not None
    # score_breakdown sums to the headline score
    assert sum(result.score.score_breakdown.model_dump().values()) == result.score.score


async def test_get_returns_persisted_result() -> None:
    job = make_job()
    service, *_ = _service(jobs=[job])
    await service.analyze(user_id=job.user_id, job_id=job.id)
    fetched = await service.get(user_id=job.user_id, job_id=job.id)
    assert fetched.analysis.provider == "mock"
    assert fetched.score.profile_version == DEFAULT_FREELANCER_PROFILE.version


async def test_analyze_unknown_job_raises_not_found() -> None:
    service, *_ = _service(jobs=[])
    job = make_job()  # not added to the repo
    with pytest.raises(NotFoundError):
        await service.analyze(user_id=job.user_id, job_id=job.id)


async def test_get_before_analyze_raises_not_found() -> None:
    job = make_job()
    service, *_ = _service(jobs=[job])
    with pytest.raises(NotFoundError):
        await service.get(user_id=job.user_id, job_id=job.id)


async def test_reanalyze_upserts_in_place() -> None:
    job = make_job()
    service, _analyses, _scores = _service(jobs=[job])
    first = await service.analyze(user_id=job.user_id, job_id=job.id)
    second = await service.analyze(user_id=job.user_id, job_id=job.id)
    # same row id across runs (upsert, not insert)
    assert first.analysis.id == second.analysis.id
    assert first.score.id == second.score.id


class _BadProvider:
    name = "bad"
    model = "bad"

    async def complete_json(self, *, system_prompt: str, user_prompt: str):
        return AIRawResponse(data={"summary": ""}, provider=self.name, model=self.model)


class _ExplodingProvider:
    name = "exploding"
    model = "exploding"

    async def complete_json(self, *, system_prompt: str, user_prompt: str):
        raise AIProviderResponseError("provider returned 500")


async def test_invalid_provider_payload_raises_analysis_failed() -> None:
    job = make_job()
    service, *_ = _service(provider=_BadProvider(), jobs=[job])
    with pytest.raises(AnalysisFailedError):
        await service.analyze(user_id=job.user_id, job_id=job.id)


async def test_provider_error_raises_analysis_failed() -> None:
    job = make_job()
    service, *_ = _service(provider=_ExplodingProvider(), jobs=[job])
    with pytest.raises(AnalysisFailedError):
        await service.analyze(user_id=job.user_id, job_id=job.id)
