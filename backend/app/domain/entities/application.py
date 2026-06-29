from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID


class ApplicationStatus(StrEnum):
    draft = "draft"
    applied = "applied"
    viewed = "viewed"
    interview = "interview"
    offer = "offer"
    won = "won"
    rejected = "rejected"
    withdrawn = "withdrawn"
    completed = "completed"


TERMINAL_STATUSES: frozenset[ApplicationStatus] = frozenset(
    {ApplicationStatus.rejected, ApplicationStatus.withdrawn, ApplicationStatus.completed}
)


# Maps each status to the column that records its first-set timestamp.
STATUS_TIMESTAMP_FIELD: dict[ApplicationStatus, str] = {
    ApplicationStatus.applied: "applied_at",
    ApplicationStatus.viewed: "viewed_at",
    ApplicationStatus.interview: "interview_at",
    ApplicationStatus.offer: "offer_at",
    ApplicationStatus.won: "won_at",
    ApplicationStatus.rejected: "rejected_at",
    ApplicationStatus.withdrawn: "withdrawn_at",
    ApplicationStatus.completed: "completed_at",
}


@dataclass(slots=True)
class Application:
    """Pure domain entity for a tracked application."""

    id: UUID
    user_id: UUID
    job_id: UUID
    status: ApplicationStatus
    proposal_id: UUID | None = None
    resume_id: UUID | None = None
    portfolio_ids: list[UUID] = field(default_factory=list)

    applied_at: datetime | None = None
    viewed_at: datetime | None = None
    interview_at: datetime | None = None
    offer_at: datetime | None = None
    won_at: datetime | None = None
    rejected_at: datetime | None = None
    withdrawn_at: datetime | None = None
    completed_at: datetime | None = None

    contract_amount: Decimal | None = None
    client_response: str | None = None
    rejection_reason: str | None = None
    notes: str | None = None
    snapshot: dict[str, Any] | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    @property
    def is_active(self) -> bool:
        return not self.is_terminal


@dataclass(slots=True)
class ApplicationHistoryEntry:
    id: UUID
    application_id: UUID
    user_id: UUID | None
    from_status: str | None
    to_status: str
    note: str | None
    created_at: datetime
