from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

Complexity = Literal["low", "medium", "high"]
RiskLevel = Literal["low", "medium", "high"]
Severity = Literal["low", "medium", "high"]
Seniority = Literal["junior", "mid", "senior", "lead", "staff", "principal"]
BudgetAssessment = Literal["low", "reasonable", "high", "unclear"]
Recommendation = Literal["Strong Apply", "Apply", "Maybe", "Skip"]
Confidence = Literal["high", "medium", "low"]

StackCategory = Literal[
    "tech_stack",
    "architecture",
    "cloud_platform",
    "ai_llm",
    "authentication",
    "billing",
    "integrations",
    "database",
    "devops",
    "testing",
    "deployment",
    "security",
    "nice_to_have",
]

# LLMs reliably slip on singular/plural and on a handful of stylistic
# variants (`auth`, `db`, `ci/cd`, etc.). Normalizing here is cheap and
# avoids rejecting an entire analysis because one row uses a near-miss
# label. The map is intentionally tight — only safe, unambiguous aliases.
_STACK_CATEGORY_ALIASES: dict[str, str] = {
    "integration": "integrations",
    "integration_partners": "integrations",
    "third_party": "integrations",
    "third_party_integrations": "integrations",
    "auth": "authentication",
    "iam": "authentication",
    "db": "database",
    "databases": "database",
    "storage": "database",
    "ci_cd": "devops",
    "ci/cd": "devops",
    "cicd": "devops",
    "infra": "devops",
    "infrastructure": "devops",
    "cloud": "cloud_platform",
    "platform": "cloud_platform",
    "ai": "ai_llm",
    "llm": "ai_llm",
    "ml": "ai_llm",
    "machine_learning": "ai_llm",
    "tests": "testing",
    "qa": "testing",
    "deploy": "deployment",
    "release": "deployment",
    "appsec": "security",
    "infosec": "security",
    "payments": "billing",
    "subscription": "billing",
    "tech": "tech_stack",
    "stack": "tech_stack",
    "languages": "tech_stack",
    "language": "tech_stack",
    "frameworks": "tech_stack",
    "framework": "tech_stack",
    "nice_to_have": "nice_to_have",
    "nice-to-have": "nice_to_have",
    "optional": "nice_to_have",
    "bonus": "nice_to_have",
}


class StackRequirementSchema(BaseModel):
    """One structured stack signal — category + canonical name + 1–5 star importance."""

    model_config = ConfigDict(extra="ignore")

    category: StackCategory
    name: str = Field(min_length=1, max_length=80)
    importance: int = Field(ge=1, le=5)

    @field_validator("category", mode="before")
    @classmethod
    def _normalize_category(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        key = value.strip().lower().replace(" ", "_").replace("-", "_")
        # If the LLM gave us a known canonical value, pass it through. If
        # we recognize an alias, swap it. Otherwise let the literal check
        # raise — there are no silent fallbacks here.
        return _STACK_CATEGORY_ALIASES.get(key, key)


class RiskItemSchema(BaseModel):
    """A single risk the LLM identified, with severity + mitigation guidance."""

    model_config = ConfigDict(extra="ignore")

    risk: str = Field(min_length=1)
    severity: Severity
    mitigation: str = Field(min_length=1)


class JobAnalysisSchema(BaseModel):
    """The strict schema every AI provider must return.

    Provider responses are JSON-parsed and validated against this model. Free-text
    parsing is forbidden — if a provider returns malformed JSON it raises and is
    retried/aborted upstream.
    """

    model_config = ConfigDict(extra="ignore")

    summary: str = Field(min_length=1, max_length=2000)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    business_domain: str | None = None
    seniority_level: Seniority | None = None
    complexity: Complexity = "medium"
    estimated_hours_min: int | None = Field(default=None, ge=0, le=10_000)
    estimated_hours_max: int | None = Field(default=None, ge=0, le=10_000)
    budget_assessment: BudgetAssessment = "unclear"
    client_intent: str | None = None
    hidden_requirements: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    risks: list[RiskItemSchema] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    green_flags: list[str] = Field(default_factory=list)
    questions_to_ask_client: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = "medium"
    communication_required: str | None = None
    stack_requirements: list[StackRequirementSchema] = Field(default_factory=list)


class JobAnalysisRead(BaseModel):
    """API representation of a stored analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    summary: str | None
    required_skills: list[str]
    preferred_skills: list[str]
    technologies: list[str]
    business_domain: str | None
    seniority: str | None
    complexity: str | None
    estimated_hours_min: int | None
    estimated_hours_max: int | None
    budget_assessment: str | None
    client_intent: str | None
    hidden_requirements: list[str]
    expected_deliverables: list[str]
    risks: list[RiskItemSchema]
    red_flags: list[str]
    green_flags: list[str]
    questions_to_ask_client: list[str]
    risk_level: str | None
    communication_required: str | None
    provider: str | None
    model: str | None
    prompt_version: str | None
    stack_requirements: list[StackRequirementSchema] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ScoreBreakdown(BaseModel):
    technical_fit: int
    domain_fit: int
    proposal_count: int
    budget_attractiveness: int
    client_quality: int
    estimated_effort: int
    risk_level: int
    strategic_value: int


class OpportunityScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    analysis_id: UUID
    score: int
    recommendation: Recommendation
    confidence: Confidence
    score_breakdown: ScoreBreakdown
    reasoning: str
    profile_version: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class JobAnalysisResponse(BaseModel):
    """Combined payload returned by POST /jobs/{id}/analyze and GET /jobs/{id}/analysis."""

    analysis: JobAnalysisRead
    score: OpportunityScoreRead
