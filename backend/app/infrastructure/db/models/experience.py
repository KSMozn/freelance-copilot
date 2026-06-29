from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base

EMPLOYMENT_TYPES = ("full_time", "contract", "freelance", "internship", "part_time")
EXPERIENCE_SOURCES = ("cv", "linkedin", "manual", "backfill")


class Experience(Base):
    """A work-history item — company × role × dates × summary.

    Populated from CV uploads, LinkedIn PDF parsing, or manual entry. The
    canonical "what I've done" record that personas filter / emphasize.
    """

    __tablename__ = "experiences"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(160), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(
        Enum(*EMPLOYMENT_TYPES, name="employment_type"), nullable=True
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        Enum(*EXPERIENCE_SOURCES, name="experience_source"),
        nullable=False,
        default="manual",
    )
    source_ref: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ExperienceSkill(Base):
    __tablename__ = "experience_skills"

    experience_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("experiences.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skill_catalog.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)


class ExperienceAchievement(Base):
    __tablename__ = "experience_achievements"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    experience_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("experiences.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    metric_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    metric_unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
