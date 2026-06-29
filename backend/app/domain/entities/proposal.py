from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(slots=True)
class Milestone:
    name: str
    description: str
    estimated_hours: float | None = None


@dataclass(slots=True)
class ProposalDiagram:
    """One Mermaid diagram emitted with the proposal.

    `kind` ∈ {'system', 'sequence'} — the proposal generator emits up to one
    of each. `mermaid` is the raw Mermaid source the UI renders inline.
    """

    kind: str
    title: str
    mermaid: str


@dataclass(slots=True)
class ImplementationWeek:
    """One week of the calendar-shaped delivery plan.

    `focus` is the spec's phase label ("Authentication", "Billing", "AI",
    "Admin", "Deployment", "Hardening"). `deliverables` are 1–3 concrete
    things that ship by end-of-week.
    """

    week: int
    focus: str
    summary: str
    deliverables: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProposalStrategy:
    """The angle the proposal leads with, decided BEFORE writing the body.

    `angle` is one of: leadership, hands_on_coding, ai, architecture,
    fast_delivery, enterprise, startup_mindset. `rationale` is a one-sentence
    justification grounded in the job context. `emphasis_points` are 2–4
    bullet hints the writer used to shape the body and double as the
    user-facing "why this angle" explanation in the UI.
    """

    angle: str
    rationale: str
    emphasis_points: list[str]


@dataclass(slots=True)
class Proposal:
    """Pure domain representation of a generated (and optionally edited) proposal."""

    id: UUID
    user_id: UUID
    job_id: UUID
    body: str
    title: str | None = None
    short_body: str | None = None
    resume_id: UUID | None = None
    portfolio_ids: list[UUID] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    milestones: list[Milestone] = field(default_factory=list)
    delivery_approach: list[str] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    quality_score: int | None = None
    quality_breakdown: dict[str, int] | None = None
    quality_warnings: list[str] = field(default_factory=list)
    strategy: ProposalStrategy | None = None
    implementation_plan: list[ImplementationWeek] = field(default_factory=list)
    diagrams: list[ProposalDiagram] = field(default_factory=list)
    prompt_version: str | None = None
    model_provider: str | None = None
    model_name: str | None = None
    raw_response: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
