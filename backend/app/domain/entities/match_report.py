from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

InterviewChance = Literal["low", "medium", "high"]
RecommendationKind = Literal[
    "project_to_build",
    "certification",
    "learning_resource",
    "github_enhancement",
    "experience_to_emphasize",
]


@dataclass(slots=True)
class GapRecommendation:
    """Actionable suggestion for closing a missing-skill gap."""

    skill: str
    kind: RecommendationKind
    suggestion: str
    effort_estimate: str  # e.g. "2-3 hours", "1-2 weeks"
    priority: int  # 1 (highest) .. 5


@dataclass(slots=True)
class MatchReport:
    id: UUID
    user_id: UUID
    job_id: UUID
    persona_id: UUID | None
    overall_match: int
    technical_fit: int
    architecture_fit: int
    domain_fit: int
    leadership_fit: int | None
    soft_skills_fit: int | None
    interview_chance: InterviewChance
    missing_critical_skills: list[dict[str, Any]] = field(default_factory=list)
    missing_recommendations: list[GapRecommendation] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)
    profile_version: str | None = None
    computed_at: datetime | None = None
