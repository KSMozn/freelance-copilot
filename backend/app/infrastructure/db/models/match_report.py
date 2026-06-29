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
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base

INTERVIEW_CHANCE = ("low", "medium", "high")


class MatchReport(Base):
    """Persisted, persona-aware match analysis.

    One row per (job, persona). The orchestrator UPSERTs by that pair so
    callers can request a "fresh compute" without piling up history.
    """

    __tablename__ = "match_reports"
    __table_args__ = (
        UniqueConstraint("job_id", "persona_id", name="uq_match_reports_job_persona"),
        Index("ix_match_reports_user_job", "user_id", "job_id"),
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
    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    persona_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=True,
    )
    overall_match: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    technical_fit: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    architecture_fit: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    domain_fit: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    leadership_fit: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    soft_skills_fit: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    interview_chance: Mapped[str] = mapped_column(
        Enum(*INTERVIEW_CHANCE, name="interview_chance"),
        nullable=False,
        default="medium",
    )
    missing_critical_skills: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    missing_recommendations: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    rationale: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    profile_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
