from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ApplicationStatusLiteral = Literal[
    "draft",
    "applied",
    "viewed",
    "interview",
    "offer",
    "won",
    "rejected",
    "withdrawn",
    "completed",
]


class CreateFromProposalRequest(BaseModel):
    """Optional body for POST /applications/from-proposal/{proposal_id}.

    Defaults to status='applied' + no note. Callers can pass status='draft'
    to stage an application without recording an applied-at timestamp.
    """

    status: ApplicationStatusLiteral = "applied"
    note: str | None = Field(default=None, max_length=1000)


class StatusUpdateRequest(BaseModel):
    to_status: ApplicationStatusLiteral
    note: str | None = Field(default=None, max_length=1000)


class ApplicationDetailsUpdate(BaseModel):
    contract_amount: Decimal | None = Field(default=None, ge=0)
    client_response: str | None = None
    rejection_reason: str | None = None
    notes: str | None = None


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    job_id: UUID
    proposal_id: UUID | None
    resume_id: UUID | None
    portfolio_ids: list[UUID]
    status: ApplicationStatusLiteral

    applied_at: datetime | None
    viewed_at: datetime | None
    interview_at: datetime | None
    offer_at: datetime | None
    won_at: datetime | None
    rejected_at: datetime | None
    withdrawn_at: datetime | None
    completed_at: datetime | None

    contract_amount: Decimal | None
    client_response: str | None
    rejection_reason: str | None
    notes: str | None
    snapshot: dict[str, Any] | None

    created_at: datetime | None = None
    updated_at: datetime | None = None


class ApplicationListResponse(BaseModel):
    items: list[ApplicationRead]
    total: int
    limit: int
    offset: int


class ApplicationHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    user_id: UUID | None
    from_status: str | None
    to_status: str
    note: str | None
    created_at: datetime
