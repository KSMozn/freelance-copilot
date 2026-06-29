from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

EmploymentType = Literal["full_time", "contract", "freelance", "internship", "part_time"]
ExperienceSource = Literal["cv", "linkedin", "manual", "backfill"]


@dataclass(slots=True)
class ExperienceAchievementEntry:
    id: UUID
    experience_id: UUID
    statement: str
    metric_value: Decimal | None = None
    metric_unit: str | None = None
    evidence_text: str | None = None


@dataclass(slots=True)
class Experience:
    id: UUID
    user_id: UUID
    company: str
    role: str
    location: str | None = None
    employment_type: EmploymentType | None = None
    start_date: date | None = None
    end_date: date | None = None  # None = currently held
    summary: str | None = None
    source: ExperienceSource = "manual"
    source_ref: UUID | None = None
    skill_ids: list[UUID] = field(default_factory=list)
    achievements: list[ExperienceAchievementEntry] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
