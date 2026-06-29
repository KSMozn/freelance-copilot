"""Phase H tracker tables — recruiter interactions, interview events,
follow-up reminders.

All three hang off ``applications`` with ``ON DELETE CASCADE`` and carry
a redundant ``user_id`` so we can tenant-scope queries without a join.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base

INTERACTION_CHANNELS = ("email", "linkedin", "phone", "in_person", "other")
INTERACTION_DIRECTIONS = ("inbound", "outbound")
INTERVIEW_FORMATS = (
    "phone_screen",
    "technical",
    "system_design",
    "behavioral",
    "onsite",
    "final",
    "other",
)
INTERVIEW_OUTCOMES = ("pending", "pass", "fail", "cancelled")


class RecruiterInteraction(Base):
    __tablename__ = "recruiter_interactions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(
        Enum(*INTERACTION_CHANNELS, name="interaction_channel", create_type=False),
        nullable=False,
        default="email",
    )
    direction: Mapped[str] = mapped_column(
        Enum(*INTERACTION_DIRECTIONS, name="interaction_direction", create_type=False),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class InterviewEvent(Base):
    __tablename__ = "interview_events"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_label: Mapped[str] = mapped_column(String(120), nullable=False)
    format: Mapped[str] = mapped_column(
        Enum(*INTERVIEW_FORMATS, name="interview_format", create_type=False),
        nullable=False,
        default="phone_screen",
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_minutes: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    interviewer_names: Mapped[str | None] = mapped_column(Text, nullable=True)
    interviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    my_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str] = mapped_column(
        Enum(*INTERVIEW_OUTCOMES, name="interview_outcome", create_type=False),
        nullable=False,
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class FollowUpReminder(Base):
    # Partial unique index on `(user_id, due_at) WHERE completed_at IS NULL`
    # is created in migration 0026 — not declared at the model layer because
    # SQLAlchemy's text-based partial index DSL conflicts with hand-written
    # alembic migrations.
    __tablename__ = "follow_up_reminders"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    channel: Mapped[str | None] = mapped_column(
        Enum(*INTERACTION_CHANNELS, name="interaction_channel", create_type=False),
        nullable=True,
    )
    note: Mapped[str] = mapped_column(Text, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
