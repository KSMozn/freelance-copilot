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
class CompanyResearch:
    """Structured research about the client's company / product, extracted
    from their website + cross-referenced URLs. Used to personalize proposals.
    """

    source_url: str
    business_domain: str | None
    product_summary: str | None
    target_customers: str | None
    existing_stack: list[str] = field(default_factory=list)
    funding_signals: str | None = None
    likely_architecture: str | None = None
    personalization_hook: str | None = None  # "I noticed your product focuses on …"
    fetched_at: datetime | None = None


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
    client_research: CompanyResearch | None = None
