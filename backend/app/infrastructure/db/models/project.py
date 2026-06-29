from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base

PROJECT_ORIGINS = ("repo", "portfolio", "cv_extracted", "manual")


class Project(Base):
    """A discrete piece of work the user has shipped.

    Subsumes the concept of "portfolio entry" and "scanned repository" — both
    backfill into this table (via `origin = portfolio` or `origin = repo`) so
    the recommendation engine and personas have a single surface.
    """

    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_user_repo", "user_id", "repo_id"),
        Index("ix_projects_user_portfolio", "user_id", "portfolio_id"),
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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str | None] = mapped_column(String(160), nullable=True)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    repo_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="SET NULL"),
        nullable=True,
    )
    portfolio_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="SET NULL"),
        nullable=True,
    )
    origin: Mapped[str] = mapped_column(
        Enum(*PROJECT_ORIGINS, name="project_origin"),
        nullable=False,
        default="manual",
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


class ProjectSkill(Base):
    __tablename__ = "project_skills"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skill_catalog.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProjectAchievement(Base):
    __tablename__ = "project_achievements"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    metric_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    metric_unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
