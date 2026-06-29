from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

InterviewChanceLiteral = Literal["low", "medium", "high"]
RecommendationKindLiteral = Literal[
    "project_to_build",
    "certification",
    "learning_resource",
    "github_enhancement",
    "experience_to_emphasize",
]


class GapRecommendationRead(BaseModel):
    skill: str
    kind: RecommendationKindLiteral
    suggestion: str
    effort_estimate: str
    priority: int = Field(ge=1, le=5)


class MatchReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    job_id: UUID
    persona_id: UUID | None
    overall_match: int = Field(ge=0, le=100)
    technical_fit: int = Field(ge=0, le=100)
    architecture_fit: int = Field(ge=0, le=100)
    domain_fit: int = Field(ge=0, le=100)
    # Null when the job doesn't carry leadership / soft signals — UI should
    # render these as "not applicable" rather than 0%.
    leadership_fit: int | None = Field(default=None, ge=0, le=100)
    soft_skills_fit: int | None = Field(default=None, ge=0, le=100)
    interview_chance: InterviewChanceLiteral
    missing_critical_skills: list[dict[str, Any]] = Field(default_factory=list)
    missing_recommendations: list[GapRecommendationRead] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)
    profile_version: str | None = None
    computed_at: datetime | None = None
