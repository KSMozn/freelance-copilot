from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.domain.entities.job import BudgetType, JobStatus


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


class JobListResponse(BaseModel):
    items: list[JobRead]
    total: int
    limit: int
    offset: int
