from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

ProjectOrigin = Literal["repo", "portfolio", "cv_extracted", "manual"]


@dataclass(slots=True)
class ProjectAchievementEntry:
    id: UUID
    project_id: UUID
    statement: str
    metric_value: Decimal | None = None
    metric_unit: str | None = None
    evidence_text: str | None = None


@dataclass(slots=True)
class Project:
    """Unified "thing I built." Subsumes portfolios + scanned repos.

    Existing rows from `portfolios` and `repositories` are backfilled into
    this table via origin = `portfolio` / `repo` and the corresponding
    `portfolio_id` / `repo_id` link. New surfaces (CV-extracted projects,
    manually added projects) join the same shape.
    """

    id: UUID
    user_id: UUID
    name: str
    summary: str | None = None
    role: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    repo_id: UUID | None = None
    portfolio_id: UUID | None = None
    origin: ProjectOrigin = "manual"
    skill_ids: list[UUID] = field(default_factory=list)
    achievements: list[ProjectAchievementEntry] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
