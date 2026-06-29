from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base

OUTPUT_KINDS = (
    "upwork_proposal",
    "cover_letter",
    "recruiter_reply",
    "linkedin_message",
    "consulting_proposal",
    "screening_answer",
    "resume_tailored",
)


class Output(Base):
    """Generic generated artifact.

    Subsumes "anything an AI produced about a job" — cover letters, Upwork
    proposals, recruiter replies, LinkedIn DMs, consulting proposals,
    screening answers, tailored resumes. Per-kind specialisation lives in
    the prompt templates, not in extra tables.
    """

    __tablename__ = "outputs"
    __table_args__ = (
        Index("ix_outputs_user_job", "user_id", "job_id"),
        Index("ix_outputs_user_kind_created", "user_id", "kind", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    persona_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="SET NULL"),
        nullable=True,
    )
    job_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=True,
    )
    kind: Mapped[str] = mapped_column(
        Enum(*OUTPUT_KINDS, name="output_kind"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    citations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    tone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ai_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
