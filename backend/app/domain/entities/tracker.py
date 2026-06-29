from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

InteractionChannel = Literal["email", "linkedin", "phone", "in_person", "other"]
InteractionDirection = Literal["inbound", "outbound"]
InterviewFormat = Literal[
    "phone_screen",
    "technical",
    "system_design",
    "behavioral",
    "onsite",
    "final",
    "other",
]
InterviewOutcome = Literal["pending", "pass", "fail", "cancelled"]


@dataclass(slots=True)
class RecruiterInteraction:
    id: UUID
    application_id: UUID
    user_id: UUID
    channel: InteractionChannel
    direction: InteractionDirection
    occurred_at: datetime
    contact_name: str | None = None
    summary: str | None = None
    raw_content: str | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class InterviewEvent:
    id: UUID
    application_id: UUID
    user_id: UUID
    round_label: str
    format: InterviewFormat
    scheduled_at: datetime | None = None
    duration_minutes: int | None = None
    interviewer_names: str | None = None
    interviewer_notes: str | None = None
    my_feedback: str | None = None
    outcome: InterviewOutcome = "pending"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class FollowUpReminder:
    id: UUID
    application_id: UUID
    user_id: UUID
    due_at: datetime
    note: str
    channel: InteractionChannel | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
