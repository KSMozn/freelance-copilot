from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


class BudgetType(StrEnum):
    fixed = "fixed"
    hourly = "hourly"


class JobStatus(StrEnum):
    new = "new"
    shortlisted = "shortlisted"
    applied = "applied"
    ignored = "ignored"
    archived = "archived"


@dataclass(slots=True)
class Job:
    id: UUID
    user_id: UUID
    title: str
    description: str
    status: JobStatus
    source_hash: str
    version: int
    imported_at: datetime
    created_at: datetime
    updated_at: datetime
    source_url: str | None = None
    budget_type: BudgetType | None = None
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    currency: str = "USD"
    proposal_count: int | None = None
    client_id: UUID | None = None
    tags: list[str] = field(default_factory=list)
