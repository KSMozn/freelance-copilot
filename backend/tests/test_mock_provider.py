from app.application.dto.analysis_dto import JobAnalysisSchema
from app.application.services.prompts import SYSTEM_PROMPT, build_user_prompt
from app.infrastructure.ai.mock_provider import MockAIProvider


async def test_mock_provider_returns_schema_valid_payload() -> None:
    provider = MockAIProvider()
    user_prompt = build_user_prompt(
        title="Build a FastAPI + Postgres backend with RAG",
        description=(
            "Need Python 3.13, FastAPI, PostgreSQL, pgvector, Docker, AWS deployment. "
            "AI SaaS company. Long term collaboration possible."
        ),
        budget="fixed USD 3000-5000",
        proposal_count=8,
    )
    raw = await provider.complete_json(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)

    assert raw.provider == "mock"
    schema = JobAnalysisSchema.model_validate(raw.data)
    # extracted recognisable skills from the prompt body
    skills_lower = [s.lower() for s in schema.required_skills + schema.technologies]
    assert "python" in skills_lower
    assert "fastapi" in skills_lower


async def test_mock_provider_flags_urgent_language() -> None:
    provider = MockAIProvider()
    user_prompt = build_user_prompt(
        title="ASAP small fix",
        description="Urgent — need this done ASAP, tight deadline.",
        budget="unspecified",
        proposal_count=2,
    )
    raw = await provider.complete_json(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
    schema = JobAnalysisSchema.model_validate(raw.data)
    assert schema.red_flags, "expected at least one red flag for urgent language"
    assert schema.risk_level in ("medium", "high")


async def test_mock_provider_handles_sparse_description() -> None:
    provider = MockAIProvider()
    user_prompt = build_user_prompt(
        title="Help with website",
        description="Need help.",
        budget="unspecified",
        proposal_count="unknown",
    )
    raw = await provider.complete_json(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
    schema = JobAnalysisSchema.model_validate(raw.data)
    assert schema.budget_assessment == "unclear"
    # missing scope detail should surface as a risk
    assert any("scope" in r.risk.lower() or "deliverable" in r.risk.lower() for r in schema.risks)
