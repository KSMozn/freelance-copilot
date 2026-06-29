from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

InterviewChance = Literal["high", "medium", "low"]


class JobConfidenceReport(BaseModel):
    """Multi-dimensional fit signal for "will this proposal land?"

    Composed from the existing services rather than recomputed from scratch:
      - Technical match  ← SkillEvidenceService (importance-weighted coverage)
      - Domain match     ← best domain_overlap across matched portfolios + repos
      - Architecture     ← best semantic similarity across matched portfolios + repos
      - Overall match    ← weighted blend of the three
      - Interview chance ← bucketed from overall + opportunity_score
    """

    model_config = ConfigDict(extra="ignore")

    job_id: UUID

    overall_match: int = Field(ge=0, le=100)
    technical_match: int = Field(ge=0, le=100)
    domain_match: int = Field(ge=0, le=100)
    architecture_match: int = Field(ge=0, le=100)

    missing_critical_skills: list[str] = Field(default_factory=list)
    interview_chance: InterviewChance
    rationale: list[str] = Field(default_factory=list)
