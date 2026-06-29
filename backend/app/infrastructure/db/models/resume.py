from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, TimestampMixin, UUIDPKMixin


class Resume(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "resumes"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(160), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    seniority_level: Mapped[str | None] = mapped_column(String(40), nullable=True)

    primary_skills: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    secondary_skills: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    industries: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    domains: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    achievements: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    project_highlights: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    keywords: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ResumeSkill(Base):
    """Legacy m2m kept around for future scoring use. Not populated in Phase 4."""

    __tablename__ = "resume_skills"

    resume_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=1)
