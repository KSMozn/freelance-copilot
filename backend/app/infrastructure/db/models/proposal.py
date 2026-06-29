from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, TimestampMixin, UUIDPKMixin


class Proposal(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "proposals"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
    )
    portfolio_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    short_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    questions: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    milestones: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    delivery_approach: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    risk_notes: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quality_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    quality_warnings: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    strategy: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    implementation_plan: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    diagrams: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    model_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
