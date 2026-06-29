from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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


class StackRequirementSchema(BaseModel):
    """One structured stack signal — category + canonical name + 1–5 star importance."""

    model_config = ConfigDict(extra="ignore")

    category: StackCategory
    name: str = Field(min_length=1, max_length=80)
    importance: int = Field(ge=1, le=5)


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
