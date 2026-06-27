from decimal import Decimal

from app.application.dto.analysis_dto import JobAnalysisSchema, RiskItemSchema
from app.application.services.scoring_service import ScoringService
from app.domain.profiles.freelancer_profile import DEFAULT_FREELANCER_PROFILE
from tests.factories import make_job


def _schema(**overrides):  # type: ignore[no-untyped-def]
    base = dict(
        summary="A backend gig needing Python and FastAPI.",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        preferred_skills=["Docker"],
        technologies=["Python", "FastAPI", "PostgreSQL", "Docker"],
        business_domain="AI SaaS",
        seniority_level="senior",
        complexity="medium",
        estimated_hours_min=20,
        estimated_hours_max=40,
        budget_assessment="reasonable",
        client_intent="Build MVP backend",
        hidden_requirements=[],
        deliverables=["Working backend", "Deployment notes"],
        risks=[
            RiskItemSchema(
                risk="Tight timeline",
                severity="medium",
                mitigation="Pin down milestones",
            ).model_dump()
        ],
        red_flags=[],
        green_flags=["Clear stack"],
        questions_to_ask_client=["Acceptance criteria?"],
        risk_level="low",
        communication_required="Weekly sync",
    )
    base.update(overrides)
    return JobAnalysisSchema.model_validate(base)


def test_strong_match_yields_strong_apply() -> None:
    scoring = ScoringService(DEFAULT_FREELANCER_PROFILE)
    job = make_job(proposal_count=4, budget_min=Decimal("3000"), budget_max=Decimal("5000"))
    result = scoring.score(job=job, analysis=_schema())

    assert result.score >= 80
    assert result.recommendation == "Strong Apply"
    assert result.confidence in ("high", "medium")

    bd = result.score_breakdown
    assert sum(bd.values()) == result.score
    # technical_fit is capped at the profile weight
    weights = DEFAULT_FREELANCER_PROFILE.weights
    for dim, value in bd.items():
        assert 0 <= value <= weights[dim], f"{dim} exceeded its max weight"


def test_skip_for_misaligned_job() -> None:
    scoring = ScoringService(DEFAULT_FREELANCER_PROFILE)
    job = make_job(
        proposal_count=80,  # high competition
        budget_min=None,
        budget_max=None,
    )
    result = scoring.score(
        job=job,
        analysis=_schema(
            required_skills=["WordPress", "PHP"],
            preferred_skills=[],
            technologies=["WordPress", "PHP"],
            business_domain="local restaurant",
            budget_assessment="low",
            risks=[
                RiskItemSchema(
                    risk="Unclear scope",
                    severity="high",
                    mitigation="Clarify before bidding",
                ).model_dump(),
            ],
            red_flags=["No clear deliverables"],
            risk_level="high",
        ),
    )
    assert result.score < 50
    assert result.recommendation == "Skip"


def test_proposal_count_buckets() -> None:
    scoring = ScoringService(DEFAULT_FREELANCER_PROFILE)
    schema = _schema()
    points = {
        2: 20,
        5: 20,
        10: 16,
        20: 12,
        30: 8,
        50: 4,
        100: 2,
    }
    for n, expected in points.items():
        job = make_job(proposal_count=n)
        result = scoring.score(job=job, analysis=schema)
        assert result.score_breakdown["proposal_count"] == expected, (n, expected)


def test_unknown_proposal_count_is_neutral() -> None:
    scoring = ScoringService(DEFAULT_FREELANCER_PROFILE)
    job = make_job(proposal_count=None)
    result = scoring.score(job=job, analysis=_schema())
    assert result.score_breakdown["proposal_count"] == 10


def test_strategic_value_counts_priority_hits() -> None:
    scoring = ScoringService(DEFAULT_FREELANCER_PROFILE)
    job = make_job()
    no_hits = scoring.score(
        job=job,
        analysis=_schema(
            summary="Generic web app.",
            client_intent=None,
            business_domain=None,
            required_skills=["Python"],
            technologies=["Python"],
        ),
    )
    many_hits = scoring.score(
        job=job,
        analysis=_schema(
            summary="RAG over PDFs with backend API and automation.",
            client_intent="AI implementation for data processing",
        ),
    )
    assert many_hits.score_breakdown["strategic_value"] > no_hits.score_breakdown["strategic_value"]
