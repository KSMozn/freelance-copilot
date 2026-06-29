from uuid import uuid4

from app.application.dto.analysis_dto import ScoreBreakdown
from app.application.dto.portfolio_dto import PortfolioMatch, PortfolioMatchesResponse
from app.application.dto.resume_dto import (
    ResumeRecommendation,
    ResumeRecommendationsResponse,
)
from app.application.services.proposal_context import (
    MAX_JOB_DESCRIPTION_CHARS,
    build_proposal_user_prompt,
)
from app.domain.entities.analysis import (
    JobAnalysis as DomainAnalysis,
    OpportunityScore as DomainScore,
    RiskItem,
)
from tests.factories import make_job


def _analysis(job_id):  # type: ignore[no-untyped-def]
    return DomainAnalysis(
        id=uuid4(),
        job_id=job_id,
        summary="A senior FastAPI + PostgreSQL backend gig with a small RAG pipeline.",
        required_skills=[f"Skill{i}" for i in range(15)],  # > MAX_REQUIRED_SKILLS
        preferred_skills=["Docker"],
        technologies=["Python", "FastAPI", "PostgreSQL"],
        business_domain="AI SaaS",
        seniority="senior",
        complexity="medium",
        estimated_hours_min=20,
        estimated_hours_max=40,
        budget_assessment="reasonable",
        client_intent="Ship MVP",
        hidden_requirements=[
            "Comfort working independently",
            "Available in EU hours",
            "Should ship tests",
            "Bonus item",  # > MAX_HIDDEN_REQUIREMENTS
        ],
        expected_deliverables=[
            "Working API",
            "Tests",
            "Docker compose",
            "Deployment notes",
            "Extra deliverable",  # > MAX_DELIVERABLES
        ],
        risks=[
            RiskItem(risk="Scope ambiguity", severity="medium", mitigation="Clarify acceptance"),
            RiskItem(risk="Tight timeline", severity="high", mitigation="Stage milestones"),
            RiskItem(risk="Unknown data shape", severity="low", mitigation="Request sample"),
            RiskItem(risk="Fourth risk", severity="low", mitigation="N/A"),
        ],
        red_flags=[],
        green_flags=["Clear stack"],
        questions_to_ask_client=["What does done look like?"],
        risk_level="medium",
        communication_required="Async + weekly sync",
        provider="mock",
        model="mock",
        prompt_version="analyzer-v1",
    )


def _score(job_id, analysis_id):  # type: ignore[no-untyped-def]
    return DomainScore(
        id=uuid4(),
        job_id=job_id,
        analysis_id=analysis_id,
        score=81,
        recommendation="Strong Apply",
        confidence="high",
        score_breakdown={
            "technical_fit": 25,
            "domain_fit": 10,
            "proposal_count": 12,
            "budget_attractiveness": 10,
            "client_quality": 6,
            "estimated_effort": 10,
            "risk_level": 6,
            "strategic_value": 2,
        },
        reasoning="Strong technical fit; some client signal missing.",
        profile_version="default-v1",
    )


def _portfolio_matches(job_id):  # type: ignore[no-untyped-def]
    return PortfolioMatchesResponse(
        job_id=job_id,
        matches=[
            PortfolioMatch(
                portfolio_id=uuid4(),
                title="AI Document Q&A — Arabic RAG Platform",
                match_score=0.71,
                semantic_score=0.81,
                skill_overlap_score=0.83,
                domain_overlap_score=0.0,
                strategic_score=0.33,
                match_reasons=["Strong skill overlap"],
                relevant_skills=["FastAPI", "RAG", "PostgreSQL"],
                relevant_domains=["Document Management"],
                suggested_talking_points=[
                    "Lead with the RAG platform.",
                    "Mention hybrid retrieval.",
                ],
            ),
            PortfolioMatch(
                portfolio_id=uuid4(),
                title="Customer 360 Analytics Platform",
                match_score=0.57,
                semantic_score=0.65,
                skill_overlap_score=0.3,
                domain_overlap_score=1.0,
                strategic_score=0.0,
                match_reasons=["Same domain"],
                relevant_skills=["PostgreSQL"],
                relevant_domains=["Enterprise SaaS"],
                suggested_talking_points=["Mention materialized views."],
            ),
            PortfolioMatch(
                portfolio_id=uuid4(),
                title="Should NOT appear (third match)",
                match_score=0.3,
                semantic_score=0.5,
                skill_overlap_score=0.1,
                domain_overlap_score=0.0,
                strategic_score=0.0,
                match_reasons=[],
                relevant_skills=[],
                relevant_domains=[],
                suggested_talking_points=[],
            ),
        ],
        embedding_provider="mock",
        embedding_model="mock-hash-1536",
        portfolio_count=3,
    )


def _resume_recs(job_id):  # type: ignore[no-untyped-def]
    return ResumeRecommendationsResponse(
        job_id=job_id,
        recommendations=[
            ResumeRecommendation(
                resume_id=uuid4(),
                title="AI / LLM Platform Resume",
                match_score=0.72,
                semantic_score=0.8,
                skill_overlap_score=0.75,
                domain_overlap_score=0.0,
                seniority_alignment_score=1.0,
                fit_reasons=["Strong skill overlap"],
                relevant_skills=["FastAPI", "RAG", "Python"],
                missing_or_weak_skills=["AWS Lambda"],
                suggested_positioning=["Lead with RAG experience"],
            ),
            ResumeRecommendation(
                resume_id=uuid4(),
                title="Engineering Manager Resume — must not appear",
                match_score=0.5,
                semantic_score=0.6,
                skill_overlap_score=0.0,
                domain_overlap_score=0.0,
                seniority_alignment_score=0.6,
                fit_reasons=[],
                relevant_skills=[],
                missing_or_weak_skills=[],
                suggested_positioning=[],
            ),
        ],
        embedding_provider="mock",
        embedding_model="mock-hash-1536",
        resume_count=2,
    )


def test_description_is_truncated_at_word_boundary() -> None:
    long_desc = " ".join(["word"] * 800)  # ~4000 chars
    job = make_job(description=long_desc)
    ctx = build_proposal_user_prompt(
        job=job,
        analysis=_analysis(job.id),
        score=_score(job.id, uuid4()),
        portfolio_matches=_portfolio_matches(job.id),
        resume_recs=_resume_recs(job.id),
    )
    # Find the description block
    block_start = ctx.user_prompt.index("Description (truncated):")
    block = ctx.user_prompt[block_start:]
    # Truncated text + ellipsis is well under the original
    assert "…" in block
    # The truncated description portion is bounded
    truncated_line_end = block.index("\n\n", block.index("\n"))
    truncated_section = block[: truncated_line_end]
    assert len(truncated_section) < MAX_JOB_DESCRIPTION_CHARS + 200


def test_only_top_n_portfolios_appear() -> None:
    job = make_job()
    ctx = build_proposal_user_prompt(
        job=job,
        analysis=_analysis(job.id),
        score=_score(job.id, uuid4()),
        portfolio_matches=_portfolio_matches(job.id),
        resume_recs=_resume_recs(job.id),
        top_portfolio_n=2,
    )
    assert "AI Document Q&A — Arabic RAG Platform" in ctx.user_prompt
    assert "Customer 360 Analytics Platform" in ctx.user_prompt
    assert "Should NOT appear" not in ctx.user_prompt


def test_only_top_resume_appears() -> None:
    job = make_job()
    ctx = build_proposal_user_prompt(
        job=job,
        analysis=_analysis(job.id),
        score=_score(job.id, uuid4()),
        portfolio_matches=_portfolio_matches(job.id),
        resume_recs=_resume_recs(job.id),
        top_resume_n=1,
    )
    assert "AI / LLM Platform Resume" in ctx.user_prompt
    assert "Engineering Manager Resume — must not appear" not in ctx.user_prompt


def test_required_skills_capped_at_max() -> None:
    job = make_job()
    ctx = build_proposal_user_prompt(
        job=job,
        analysis=_analysis(job.id),
        score=_score(job.id, uuid4()),
        portfolio_matches=_portfolio_matches(job.id),
        resume_recs=_resume_recs(job.id),
    )
    # 15 skills given, max is 8
    assert "Skill0" in ctx.user_prompt
    assert "Skill7" in ctx.user_prompt
    assert "Skill14" not in ctx.user_prompt


def test_used_ids_match_top_n() -> None:
    job = make_job()
    matches = _portfolio_matches(job.id)
    recs = _resume_recs(job.id)
    ctx = build_proposal_user_prompt(
        job=job,
        analysis=_analysis(job.id),
        score=_score(job.id, uuid4()),
        portfolio_matches=matches,
        resume_recs=recs,
        top_portfolio_n=2,
        top_resume_n=1,
    )
    assert ctx.used_portfolio_ids == [m.portfolio_id for m in matches.matches[:2]]
    assert ctx.used_resume_id == recs.recommendations[0].resume_id


def test_no_portfolio_no_resume_handled_gracefully() -> None:
    job = make_job()
    empty_matches = PortfolioMatchesResponse(
        job_id=job.id,
        matches=[],
        embedding_provider="mock",
        embedding_model="m",
        portfolio_count=0,
    )
    empty_recs = ResumeRecommendationsResponse(
        job_id=job.id,
        recommendations=[],
        embedding_provider="mock",
        embedding_model="m",
        resume_count=0,
    )
    ctx = build_proposal_user_prompt(
        job=job,
        analysis=_analysis(job.id),
        score=_score(job.id, uuid4()),
        portfolio_matches=empty_matches,
        resume_recs=empty_recs,
    )
    assert "no portfolio projects available" in ctx.user_prompt
    assert "no resume profiles available" in ctx.user_prompt
    assert ctx.used_portfolio_ids == []
    assert ctx.used_resume_id is None
