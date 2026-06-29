from decimal import Decimal
from uuid import uuid4

import pytest

from app.application.dto.application_dto import (
    ApplicationDetailsUpdate,
    CreateFromProposalRequest,
    StatusUpdateRequest,
)
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
from app.domain.entities.application import ApplicationStatus
from app.domain.exceptions import AlreadyExistsError, NotFoundError
from app.domain.profiles.freelancer_profile import DEFAULT_FREELANCER_PROFILE
from app.domain.services.application_state_machine import InvalidTransitionError
from app.infrastructure.ai.mock_embedding_provider import MockEmbeddingProvider
from app.infrastructure.ai.mock_provider import MockAIProvider
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


async def _setup(user_id=None):  # type: ignore[no-untyped-def]
    user_id = user_id or uuid4()
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
    app_repo = FakeApplicationRepository()
    history_repo = FakeApplicationHistoryRepository()
    embedding_provider = MockEmbeddingProvider()

    portfolio_svc = PortfolioService(
        portfolio_repo=portfolio_repo,
        embedding_repo=embedding_repo,
        embedding_provider=embedding_provider,
    )
    for p in portfolios:
        await portfolio_svc.ensure_embedding(p)
    resume_svc = ResumeService(
        resume_repo=resume_repo,
        embedding_repo=embedding_repo,
        embedding_provider=embedding_provider,
    )
    for r in resumes:
        await resume_svc.ensure_embedding(r)

    await JobAnalysisService(
        job_repo=job_repo,
        analysis_repo=analysis_repo,
        score_repo=score_repo,
        ai_provider=MockAIProvider(),
        scoring=ScoringService(DEFAULT_FREELANCER_PROFILE),
    ).analyze(user_id=user_id, job_id=job.id)

    matching = PortfolioMatchingService(
        job_repo=job_repo,
        portfolio_repo=portfolio_repo,
        analysis_repo=analysis_repo,
        embedding_repo=embedding_repo,
        portfolio_service=portfolio_svc,
        embedding_provider=embedding_provider,
        profile=DEFAULT_FREELANCER_PROFILE,
    )
    recs = ResumeRecommendationService(
        job_repo=job_repo,
        resume_repo=resume_repo,
        analysis_repo=analysis_repo,
        embedding_repo=embedding_repo,
        resume_service=resume_svc,
        embedding_provider=embedding_provider,
    )

    proposal = await ProposalGenerationService(
        job_repo=job_repo,
        analysis_repo=analysis_repo,
        score_repo=score_repo,
        portfolio_repo=portfolio_repo,
        portfolio_matching_service=matching,
        resume_recommendation_service=recs,
        proposal_repo=proposal_repo,
        ai_provider=MockAIProvider(),
        review_service=ProposalReviewService(),
    ).generate(user_id=user_id, job_id=job.id)

    app_svc = ApplicationService(
        application_repo=app_repo,
        history_repo=history_repo,
        job_repo=job_repo,
        proposal_repo=proposal_repo,
        resume_repo=resume_repo,
        portfolio_repo=portfolio_repo,
        score_repo=score_repo,
        portfolio_matching_service=matching,
        resume_recommendation_service=recs,
    )
    return {
        "user_id": user_id,
        "job": job,
        "proposal": proposal,
        "app_svc": app_svc,
        "app_repo": app_repo,
        "history_repo": history_repo,
    }


async def test_create_from_proposal_snapshots_job_and_proposal() -> None:
    state = await _setup()
    app = await state["app_svc"].create_from_proposal(
        user_id=state["user_id"],
        proposal_id=state["proposal"].id,
        payload=CreateFromProposalRequest(),
    )
    assert app.status == "applied"
    assert app.applied_at is not None
    assert app.snapshot is not None
    snap = app.snapshot

    # job is captured by value, not just reference
    assert snap["job"]["title"] == state["job"].title
    # proposal body verbatim
    assert snap["proposal"]["body"] == state["proposal"].body
    assert snap["proposal"]["quality_score"] == state["proposal"].quality_score
    # opportunity score breakdown present
    assert "opportunity_score" in snap
    assert snap["opportunity_score"]["score"]
    # resume + portfolio snapshots present
    assert snap["resume"]["title"] == "AI / LLM Platform Resume"
    assert len(snap["portfolio"]) >= 1
    assert snap["portfolio"][0]["title"]


async def test_snapshot_is_immutable_after_proposal_changes() -> None:
    """Editing the source proposal must not retroactively change the snapshot."""
    state = await _setup()
    app = await state["app_svc"].create_from_proposal(
        user_id=state["user_id"],
        proposal_id=state["proposal"].id,
        payload=CreateFromProposalRequest(),
    )
    original_body = state["proposal"].body

    # Mutate the underlying proposal — the snapshot must keep the original.
    state["proposal"].body = "completely rewritten by the user"

    refreshed = await state["app_svc"].get(
        user_id=state["user_id"], application_id=app.id
    )
    assert refreshed.snapshot is not None
    assert refreshed.snapshot["proposal"]["body"] == original_body


async def test_create_records_initial_history_row() -> None:
    state = await _setup()
    app = await state["app_svc"].create_from_proposal(
        user_id=state["user_id"],
        proposal_id=state["proposal"].id,
        payload=CreateFromProposalRequest(note="First-pass apply"),
    )
    history = await state["app_svc"].get_history(
        user_id=state["user_id"], application_id=app.id
    )
    assert len(history) == 1
    assert history[0].from_status is None
    assert history[0].to_status == "applied"
    assert history[0].note == "First-pass apply"


async def test_duplicate_active_application_rejected() -> None:
    state = await _setup()
    await state["app_svc"].create_from_proposal(
        user_id=state["user_id"],
        proposal_id=state["proposal"].id,
        payload=CreateFromProposalRequest(),
    )
    with pytest.raises(AlreadyExistsError):
        await state["app_svc"].create_from_proposal(
            user_id=state["user_id"],
            proposal_id=state["proposal"].id,
            payload=CreateFromProposalRequest(),
        )


async def test_terminal_status_unblocks_new_application() -> None:
    state = await _setup()
    first = await state["app_svc"].create_from_proposal(
        user_id=state["user_id"],
        proposal_id=state["proposal"].id,
        payload=CreateFromProposalRequest(),
    )
    # Withdraw the first one — should let a new one through.
    await state["app_svc"].update_status(
        user_id=state["user_id"],
        application_id=first.id,
        payload=StatusUpdateRequest(to_status="withdrawn"),
    )
    second = await state["app_svc"].create_from_proposal(
        user_id=state["user_id"],
        proposal_id=state["proposal"].id,
        payload=CreateFromProposalRequest(),
    )
    assert second.id != first.id


async def test_status_progression_sets_timestamps() -> None:
    state = await _setup()
    app = await state["app_svc"].create_from_proposal(
        user_id=state["user_id"],
        proposal_id=state["proposal"].id,
        payload=CreateFromProposalRequest(),
    )
    assert app.applied_at is not None
    assert app.viewed_at is None

    # applied → viewed
    app = await state["app_svc"].update_status(
        user_id=state["user_id"],
        application_id=app.id,
        payload=StatusUpdateRequest(to_status="viewed", note="Client opened the link."),
    )
    assert app.viewed_at is not None

    # viewed → interview
    app = await state["app_svc"].update_status(
        user_id=state["user_id"],
        application_id=app.id,
        payload=StatusUpdateRequest(to_status="interview"),
    )
    assert app.interview_at is not None

    # interview → offer → won → completed
    app = await state["app_svc"].update_status(
        user_id=state["user_id"],
        application_id=app.id,
        payload=StatusUpdateRequest(to_status="offer"),
    )
    assert app.offer_at is not None
    app = await state["app_svc"].update_status(
        user_id=state["user_id"],
        application_id=app.id,
        payload=StatusUpdateRequest(to_status="won"),
    )
    assert app.won_at is not None
    app = await state["app_svc"].update_status(
        user_id=state["user_id"],
        application_id=app.id,
        payload=StatusUpdateRequest(to_status="completed"),
    )
    assert app.completed_at is not None

    # History has 6 rows (applied + 5 transitions)
    history = await state["app_svc"].get_history(
        user_id=state["user_id"], application_id=app.id
    )
    assert len(history) == 6


async def test_invalid_status_transition_rejected() -> None:
    state = await _setup()
    app = await state["app_svc"].create_from_proposal(
        user_id=state["user_id"],
        proposal_id=state["proposal"].id,
        payload=CreateFromProposalRequest(),
    )
    with pytest.raises(InvalidTransitionError):
        await state["app_svc"].update_status(
            user_id=state["user_id"],
            application_id=app.id,
            payload=StatusUpdateRequest(to_status="won"),
        )


async def test_update_details_patches_fields() -> None:
    state = await _setup()
    app = await state["app_svc"].create_from_proposal(
        user_id=state["user_id"],
        proposal_id=state["proposal"].id,
        payload=CreateFromProposalRequest(),
    )
    updated = await state["app_svc"].update_details(
        user_id=state["user_id"],
        application_id=app.id,
        payload=ApplicationDetailsUpdate(
            contract_amount=Decimal("3500.00"),
            client_response="Wants to do a call Tuesday.",
            notes="Sent a calendar link.",
        ),
    )
    assert updated.contract_amount == Decimal("3500.00")
    assert updated.client_response == "Wants to do a call Tuesday."
    assert updated.notes == "Sent a calendar link."


async def test_list_filters_by_status() -> None:
    state = await _setup()
    app = await state["app_svc"].create_from_proposal(
        user_id=state["user_id"],
        proposal_id=state["proposal"].id,
        payload=CreateFromProposalRequest(),
    )
    # Add a second application by withdrawing the first and creating again.
    await state["app_svc"].update_status(
        user_id=state["user_id"],
        application_id=app.id,
        payload=StatusUpdateRequest(to_status="withdrawn"),
    )
    await state["app_svc"].create_from_proposal(
        user_id=state["user_id"],
        proposal_id=state["proposal"].id,
        payload=CreateFromProposalRequest(),
    )

    all_apps = await state["app_svc"].list(
        user_id=state["user_id"],
        status=None,
        search=None,
        limit=10,
        offset=0,
    )
    assert all_apps.total == 2

    only_withdrawn = await state["app_svc"].list(
        user_id=state["user_id"],
        status=ApplicationStatus.withdrawn,
        search=None,
        limit=10,
        offset=0,
    )
    assert only_withdrawn.total == 1


async def test_get_unknown_application_raises() -> None:
    state = await _setup()
    with pytest.raises(NotFoundError):
        await state["app_svc"].get(
            user_id=state["user_id"], application_id=uuid4()
        )


async def test_create_from_unknown_proposal_raises() -> None:
    state = await _setup()
    with pytest.raises(NotFoundError):
        await state["app_svc"].create_from_proposal(
            user_id=state["user_id"],
            proposal_id=uuid4(),
            payload=CreateFromProposalRequest(),
        )


async def test_draft_then_apply_sets_applied_at() -> None:
    state = await _setup()
    app = await state["app_svc"].create_from_proposal(
        user_id=state["user_id"],
        proposal_id=state["proposal"].id,
        payload=CreateFromProposalRequest(status="draft"),
    )
    assert app.status == "draft"
    assert app.applied_at is None
    app = await state["app_svc"].update_status(
        user_id=state["user_id"],
        application_id=app.id,
        payload=StatusUpdateRequest(to_status="applied"),
    )
    assert app.status == "applied"
    assert app.applied_at is not None
