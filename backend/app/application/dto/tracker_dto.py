from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

InteractionChannelLiteral = Literal["email", "linkedin", "phone", "in_person", "other"]
InteractionDirectionLiteral = Literal["inbound", "outbound"]
InterviewFormatLiteral = Literal[
    "phone_screen",
    "technical",
    "system_design",
    "behavioral",
    "onsite",
    "final",
    "other",
]
InterviewOutcomeLiteral = Literal["pending", "pass", "fail", "cancelled"]


# ---- Recruiter interactions ---------------------------------------------


class RecruiterInteractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    user_id: UUID
    channel: InteractionChannelLiteral
    direction: InteractionDirectionLiteral
    occurred_at: datetime
    contact_name: str | None = None
    summary: str | None = None
    raw_content: str | None = None
    created_at: datetime | None = None


class RecruiterInteractionCreate(BaseModel):
    channel: InteractionChannelLiteral = "email"
    direction: InteractionDirectionLiteral
    occurred_at: datetime
    contact_name: str | None = Field(default=None, max_length=255)
    summary: str | None = Field(default=None, max_length=4000)
    raw_content: str | None = Field(default=None, max_length=20_000)


# ---- Interview events ----------------------------------------------------


class InterviewEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    user_id: UUID
    round_label: str
    format: InterviewFormatLiteral
    scheduled_at: datetime | None = None
    duration_minutes: int | None = None
    interviewer_names: str | None = None
    interviewer_notes: str | None = None
    my_feedback: str | None = None
    outcome: InterviewOutcomeLiteral
    created_at: datetime | None = None
    updated_at: datetime | None = None


class InterviewEventCreate(BaseModel):
    round_label: str = Field(min_length=1, max_length=120)
    format: InterviewFormatLiteral = "phone_screen"
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=5, le=600)
    interviewer_names: str | None = Field(default=None, max_length=2000)


class InterviewEventUpdate(BaseModel):
    round_label: str | None = Field(default=None, min_length=1, max_length=120)
    format: InterviewFormatLiteral | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=5, le=600)
    interviewer_names: str | None = Field(default=None, max_length=2000)
    interviewer_notes: str | None = Field(default=None, max_length=20_000)
    my_feedback: str | None = Field(default=None, max_length=20_000)
    outcome: InterviewOutcomeLiteral | None = None


# ---- Follow-up reminders -------------------------------------------------


class FollowUpReminderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    user_id: UUID
    due_at: datetime
    note: str
    channel: InteractionChannelLiteral | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None


class FollowUpReminderCreate(BaseModel):
    due_at: datetime
    note: str = Field(min_length=1, max_length=2000)
    channel: InteractionChannelLiteral | None = None


# ---- Application activity bundle ----------------------------------------


class ApplicationActivityRead(BaseModel):
    """All three child lists for one application — single round-trip for
    the rebuilt detail page."""

    interactions: list[RecruiterInteractionRead] = Field(default_factory=list)
    interviews: list[InterviewEventRead] = Field(default_factory=list)
    reminders: list[FollowUpReminderRead] = Field(default_factory=list)
