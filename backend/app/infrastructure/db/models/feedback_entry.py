"""Feedback + post-download survey rows.

One table with a `kind` discriminator holds both surfaces:

  * `general` — free-text feedback submitted from the /feedback page.
    Message is required; rating and template_slug stay null.
  * `post_download` — 1..5 star rating (+ optional comment) captured
    from the survey card that appears after a CV download. Rating is
    required; message stays null unless the student added a note.

Both roll into the daily admin report; general feedback additionally
fires an immediate notification email (see FeedbackService).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base

FEEDBACK_KINDS = ("general", "post_download")


class FeedbackEntry(Base):
    __tablename__ = "feedback_entries"
    __table_args__ = (
        Index("ix_feedback_created_at_desc", "created_at"),
        Index("ix_feedback_user_created", "user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(
        Enum(*FEEDBACK_KINDS, name="feedback_kind", create_type=False),
        nullable=False,
    )

    rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_slug: Mapped[str | None] = mapped_column(String(64), nullable=True)
    screenshot_file_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("uploaded_files.id", ondelete="SET NULL"),
        nullable=True,
    )
    meta: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
