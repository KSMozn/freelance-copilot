from datetime import UTC, datetime
from uuid import uuid4

from app.application.services.proposal_prompts import BANNED_PHRASES
from app.application.services.proposal_review_service import ProposalReviewService
from app.domain.entities.analysis import JobAnalysis as DomainAnalysis
from app.domain.entities.proposal import Proposal
from tests.factories import make_portfolio


def _proposal(body: str, *, title: str | None = "Re: project — concrete plan", risk_notes=None) -> Proposal:
    return Proposal(
        id=uuid4(),
        user_id=uuid4(),
        job_id=uuid4(),
        body=body,
        title=title,
        risk_notes=list(risk_notes or []),
    )


def _analysis() -> DomainAnalysis:
    return DomainAnalysis(
        id=uuid4(),
        job_id=uuid4(),
        summary="Build a FastAPI + PostgreSQL backend with a small RAG pipeline.",
        required_skills=["Python", "FastAPI", "PostgreSQL", "Docker", "RAG"],
        preferred_skills=[],
        technologies=["Python", "FastAPI"],
        business_domain="AI SaaS",
        seniority="senior",
        complexity="medium",
        estimated_hours_min=20,
        estimated_hours_max=40,
        budget_assessment="reasonable",
        client_intent="Ship MVP",
        hidden_requirements=[],
        expected_deliverables=["API"],
        risks=[],
        red_flags=[],
        green_flags=[],
        questions_to_ask_client=[],
        risk_level="medium",
        communication_required=None,
        provider="mock",
        model="mock",
        prompt_version="analyzer-v1",
    )


GOOD_BODY = """Reading the brief, this is a focused FastAPI + PostgreSQL build \
with a small RAG layer on top, scoped to ~30 hours. I'd start with a thin \
end-to-end vertical slice in week one using Docker + pgvector so we can demo \
working software fast and surface any scope ambiguity early.

From my AI Document Q&A — Arabic RAG Platform project I'd port the hybrid \
retrieval pattern (pgvector + BM25), which fits your acceptance criteria for \
sub-200ms p95 retrieval. We'd then layer in the harder API surface and a \
small evaluation set so we're not deploying on hope.

Two flags before quoting fixed price: I want to lock acceptance criteria per \
milestone, and I'd ask for a sample of 20 representative PDFs so I can size \
the OCR step honestly. Happy to do a 20-minute call this week to align — \
here's my calendar."""

GENERIC_BODY = """I am excited to apply for this project. I have extensive \
experience and I am a perfect fit for what you need. I can help you with \
this project end to end and look forward to working with you. As an AI \
language model, I would love to apply my skills here. Please consider me."""


def test_good_proposal_scores_high() -> None:
    svc = ProposalReviewService()
    portfolios = [
        make_portfolio(title="AI Document Q&A — Arabic RAG Platform"),
    ]
    result = svc.review(
        proposal=_proposal(GOOD_BODY, risk_notes=["Clarify acceptance criteria."]),
        analysis=_analysis(),
        portfolios=portfolios,
    )
    assert result.quality_score >= 70
    assert sum(result.quality_breakdown.model_dump().values()) == result.quality_score


def test_quality_breakdown_sums_to_total_always() -> None:
    """Invariant across many inputs: per-dimension scores sum to quality_score."""
    svc = ProposalReviewService()
    for body in (GOOD_BODY, GENERIC_BODY, "", "short body."):
        proposal = _proposal(body)
        result = svc.review(proposal=proposal, analysis=_analysis(), portfolios=[])
        assert sum(result.quality_breakdown.model_dump().values()) == result.quality_score


def test_banned_phrases_emit_warnings_and_dock_score() -> None:
    svc = ProposalReviewService()
    bad = svc.review(
        proposal=_proposal(GENERIC_BODY),
        analysis=_analysis(),
        portfolios=[],
    )
    # At least one banned phrase was flagged
    assert any("Generic phrase detected" in w for w in bad.warnings)
    # Non-generic dimension is below its max
    assert bad.quality_breakdown.non_generic_wording < 10


def test_call_to_action_dimension() -> None:
    svc = ProposalReviewService()
    with_cta = svc.review(
        proposal=_proposal(GOOD_BODY),
        analysis=_analysis(),
        portfolios=[],
    )
    without_cta = svc.review(
        proposal=_proposal(
            "We will deliver this on time and in scope. The end."
        ),
        analysis=_analysis(),
        portfolios=[],
    )
    assert with_cta.quality_breakdown.call_to_action > without_cta.quality_breakdown.call_to_action


def test_portfolio_evidence_warns_when_missing() -> None:
    svc = ProposalReviewService()
    portfolios = [make_portfolio(title="AI Document Q&A — Arabic RAG Platform")]
    no_evidence = svc.review(
        proposal=_proposal("Plain text without any project names."),
        analysis=_analysis(),
        portfolios=portfolios,
    )
    assert no_evidence.quality_breakdown.portfolio_evidence == 0
    assert any("concrete project reference" in w for w in no_evidence.warnings)


def test_brevity_target_band() -> None:
    svc = ProposalReviewService()
    in_band = " ".join(["word"] * 320)
    too_long = " ".join(["word"] * 800)
    too_short = " ".join(["word"] * 80)
    a = svc.review(
        proposal=_proposal(in_band),
        analysis=_analysis(),
        portfolios=[],
    )
    b = svc.review(
        proposal=_proposal(too_long),
        analysis=_analysis(),
        portfolios=[],
    )
    c = svc.review(
        proposal=_proposal(too_short),
        analysis=_analysis(),
        portfolios=[],
    )
    assert a.quality_breakdown.brevity > b.quality_breakdown.brevity
    assert a.quality_breakdown.brevity > c.quality_breakdown.brevity


def test_max_dimension_caps() -> None:
    """Each dimension's score must never exceed its documented max."""
    svc = ProposalReviewService()
    body = (
        GOOD_BODY
        + " "
        + " ".join([f"100 hours {i}x" for i in range(5)])
    )
    result = svc.review(
        proposal=_proposal(body, risk_notes=["x"]),
        analysis=_analysis(),
        portfolios=[make_portfolio(title="AI Document Q&A — Arabic RAG Platform")],
    )
    bd = result.quality_breakdown
    assert bd.specificity <= 20
    assert bd.relevance <= 20
    assert bd.portfolio_evidence <= 15
    assert bd.clarity <= 15
    assert bd.brevity <= 10
    assert bd.non_generic_wording <= 10
    assert bd.risk_awareness <= 5
    assert bd.call_to_action <= 5


def test_banned_phrases_list_synced_with_prompt() -> None:
    """Belt-and-braces: the prompt embeds the same banned-phrase list."""
    # Spot-check that the canonical phrases from the spec are present
    for phrase in (
        "I am excited to apply",
        "I am a perfect fit",
        "I have extensive experience",
        "I can help you with this project",
        "As an AI language model",
    ):
        assert phrase in BANNED_PHRASES
