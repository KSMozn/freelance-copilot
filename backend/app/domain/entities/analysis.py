from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(slots=True)
class RiskItem:
    risk: str
    severity: str  # 'low' | 'medium' | 'high'
    mitigation: str


@dataclass(slots=True)
class JobAnalysis:
    """Pure domain entity: what the LLM extracted about a job.

    Knows nothing about how it was produced or how it is stored.
    """

    id: UUID
    job_id: UUID
    summary: str | None
    required_skills: list[str]
    preferred_skills: list[str]
    technologies: list[str]
    business_domain: str | None
    seniority: str | None
    complexity: str | None             # 'low' | 'medium' | 'high'
    estimated_hours_min: int | None
    estimated_hours_max: int | None
    budget_assessment: str | None      # 'low' | 'reasonable' | 'high' | 'unclear'
    client_intent: str | None
    hidden_requirements: list[str]
    expected_deliverables: list[str]
    risks: list[RiskItem]
    red_flags: list[str]
    green_flags: list[str]
    questions_to_ask_client: list[str]
    risk_level: str | None             # 'low' | 'medium' | 'high'
    communication_required: str | None
    provider: str | None
    model: str | None
    prompt_version: str | None
    raw_response: dict[str, Any] | None = field(default=None)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class OpportunityScore:
    id: UUID
    job_id: UUID
    analysis_id: UUID
    score: int                         # 0..100
    recommendation: str                # 'Strong Apply' | 'Apply' | 'Maybe' | 'Skip'
    confidence: str                    # 'high' | 'medium' | 'low'
    score_breakdown: dict[str, int]
    reasoning: str
    profile_version: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
