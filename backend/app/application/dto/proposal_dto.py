from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ProposalAngle = Literal[
    "leadership",
    "hands_on_coding",
    "ai",
    "architecture",
    "fast_delivery",
    "enterprise",
    "startup_mindset",
]


class ProposalStrategySchema(BaseModel):
    """The chosen angle for the proposal — decided before writing."""

    model_config = ConfigDict(extra="ignore")

    angle: ProposalAngle
    rationale: str = Field(min_length=1, max_length=500)
    emphasis_points: list[str] = Field(default_factory=list, max_length=6)


# ---- Provider output schema (validated against the AI response) ----


class MilestoneSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=600)
    estimated_hours: float | None = Field(default=None, ge=0, le=10_000)


class ImplementationWeekSchema(BaseModel):
    """One week of the calendar-shaped implementation plan."""

    model_config = ConfigDict(extra="ignore")

    week: int = Field(ge=1, le=52)
    focus: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=320)
    deliverables: list[str] = Field(default_factory=list, max_length=5)


ProposalDiagramKind = Literal["system", "sequence"]


class ProposalDiagramSchema(BaseModel):
    """One Mermaid diagram emitted with the proposal."""

    model_config = ConfigDict(extra="ignore")

    kind: ProposalDiagramKind
    title: str = Field(min_length=1, max_length=120)
    mermaid: str = Field(min_length=10, max_length=4000)


class ProposalDraftSchema(BaseModel):
    """Strict schema every AI provider must return for a proposal generation call."""

    model_config = ConfigDict(extra="ignore")

    strategy: ProposalStrategySchema
    title: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=50)
    short_body: str = Field(min_length=20)
    questions: list[str] = Field(default_factory=list, max_length=10)
    milestones: list[MilestoneSchema] = Field(default_factory=list, max_length=10)
    delivery_approach: list[str] = Field(default_factory=list, max_length=10)
    risk_notes: list[str] = Field(default_factory=list, max_length=10)
    implementation_plan: list[ImplementationWeekSchema] = Field(
        default_factory=list, max_length=12
    )
    diagrams: list[ProposalDiagramSchema] = Field(default_factory=list, max_length=4)


# ---- API DTOs ----


class MilestoneRead(BaseModel):
    name: str
    description: str
    estimated_hours: float | None = None


class ProposalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    job_id: UUID
    resume_id: UUID | None
    portfolio_ids: list[UUID]

    title: str | None
    body: str
    short_body: str | None
    questions: list[str]
    milestones: list[MilestoneRead]
    delivery_approach: list[str]
    risk_notes: list[str]

    quality_score: int | None
    quality_breakdown: dict[str, int] | None
    quality_warnings: list[str]

    strategy: ProposalStrategySchema | None = None
    implementation_plan: list[ImplementationWeekSchema] = Field(default_factory=list)
    diagrams: list[ProposalDiagramSchema] = Field(default_factory=list)
    prompt_version: str | None
    model_provider: str | None
    model_name: str | None

    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProposalGenerateRequest(BaseModel):
    """Optional knobs for the generation endpoint."""

    top_portfolio_n: int = Field(default=2, ge=0, le=5)
    top_resume_n: int = Field(default=1, ge=0, le=3)


class ProposalUpdateRequest(BaseModel):
    """Fields the user is allowed to edit on a saved proposal."""

    title: str | None = Field(default=None, max_length=300)
    body: str | None = Field(default=None, min_length=20)
    short_body: str | None = Field(default=None, min_length=20)
    questions: list[str] | None = None
    milestones: list[MilestoneRead] | None = None
    delivery_approach: list[str] | None = None
    risk_notes: list[str] | None = None


class QualityBreakdown(BaseModel):
    """Per-dimension quality score; sums to `quality_score`. Max weights are
    fixed by the deterministic review (sum = 100).
    """

    specificity: int
    relevance: int
    portfolio_evidence: int
    clarity: int
    brevity: int
    non_generic_wording: int
    risk_awareness: int
    call_to_action: int


class ProposalReviewResult(BaseModel):
    """Returned by POST /proposals/{id}/review (and embedded into ProposalRead)."""

    quality_score: int = Field(ge=0, le=100)
    quality_breakdown: QualityBreakdown
    warnings: list[str]


# Internal raw-response wrapper (kept opaque to the API layer for now)
RawResponse = dict[str, Any]
