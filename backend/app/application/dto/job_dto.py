from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.application.dto.analysis_dto import OpportunityScoreRead
from app.domain.entities.job import BudgetType, JobStatus


class CompanyResearchSchema(BaseModel):
    """Structured research about the client — extracted from their website
    and surfaced as personalization context for the proposal.
    """

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    source_url: str
    business_domain: str | None = None
    product_summary: str | None = Field(default=None, max_length=600)
    target_customers: str | None = Field(default=None, max_length=400)
    existing_stack: list[str] = Field(default_factory=list)
    funding_signals: str | None = Field(default=None, max_length=400)
    likely_architecture: str | None = Field(default=None, max_length=600)
    personalization_hook: str | None = Field(default=None, max_length=400)
    fetched_at: datetime | None = None


class CompanyResearchRequest(BaseModel):
    """User-supplied URL to research (client website / product page)."""

    url: HttpUrl


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1)
    source_url: HttpUrl | None = None
    budget_type: BudgetType | None = None
    budget_min: Decimal | None = Field(default=None, ge=0)
    budget_max: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    proposal_count: int | None = Field(default=None, ge=0)


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, min_length=1)
    source_url: HttpUrl | None = None
    budget_type: BudgetType | None = None
    budget_min: Decimal | None = Field(default=None, ge=0)
    budget_max: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    proposal_count: int | None = Field(default=None, ge=0)
    status: JobStatus | None = None


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    description: str
    source_url: str | None
    budget_type: BudgetType | None
    budget_min: Decimal | None
    budget_max: Decimal | None
    currency: str
    proposal_count: int | None
    client_id: UUID | None
    status: JobStatus
    source_hash: str
    version: int
    imported_at: datetime
    created_at: datetime
    updated_at: datetime
    opportunity_score: OpportunityScoreRead | None = None
    client_research: CompanyResearchSchema | None = None


class JobListResponse(BaseModel):
    items: list[JobRead]
    total: int
    limit: int
    offset: int
