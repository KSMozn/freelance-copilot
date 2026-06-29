from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

EvidenceSource = Literal["portfolio", "resume", "repository"]

# Inherits the same categories the analyzer emits — keeps the UI groupable on
# the same axis as `stack_requirements`.
EvidenceCategory = Literal[
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


class EvidenceItem(BaseModel):
    """One concrete piece of evidence pulled from a portfolio / resume / repo."""

    model_config = ConfigDict(extra="ignore")

    source_type: EvidenceSource
    source_id: UUID
    source_label: str  # e.g. "Customer 360 Analytics Platform" or "owner/name"
    snippet: str  # short sentence the proposal can quote verbatim


class SkillEvidence(BaseModel):
    """Evidence rollup for a single required / preferred skill."""

    model_config = ConfigDict(extra="ignore")

    name: str
    category: EvidenceCategory | None = None
    importance: int | None = Field(default=None, ge=1, le=5)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    best_snippet: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    status: Literal["strong", "weak", "missing"]


class EvidenceReport(BaseModel):
    job_id: UUID
    skills: list[SkillEvidence]
    counts: dict[str, int]  # {"strong": n, "weak": n, "missing": n}
    portfolio_count: int
    resume_count: int
    repository_count: int
