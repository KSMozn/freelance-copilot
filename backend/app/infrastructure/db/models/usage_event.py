"""SQLAlchemy model for `usage_events` — the append-only log the admin
panel reads for the Activity view and the Overview aggregates.

Kept intentionally narrow. Emit sites (coach endpoints, CV endpoints,
auth) fire-and-forget through UsageEventService.record(); no request is
allowed to slow down on a log write.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base

USAGE_EVENT_KINDS = (
    "auth.register",
    "auth.login",
    "auth.otp_request",
    "auth.otp_verify",
    "coach.draft_summary",
    "coach.proofread",
    "coach.photo",
    "coach.text",
    "coach.email",
    "cv.preview",
    "cv.pdf",
    "admin.impersonate",
    "admin.action",
    "error",
)

USAGE_EVENT_STATUSES = ("ok", "error")


class UsageEvent(Base):
    __tablename__ = "usage_events"
    __table_args__ = (
        Index("ix_usage_events_created_kind", "created_at", "kind"),
        Index("ix_usage_events_user_created", "user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    kind: Mapped[str] = mapped_column(
        Enum(*USAGE_EVENT_KINDS, name="usage_event_kind", create_type=False),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(*USAGE_EVENT_STATUSES, name="usage_event_status", create_type=False),
        nullable=False,
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
