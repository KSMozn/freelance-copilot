from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, TimestampMixin, UUIDPKMixin


class Portfolio(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "portfolios"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    long_description: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    business_domain: Mapped[str | None] = mapped_column(String(120), nullable=True)
    github_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    live_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    technologies: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    skills: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    features: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    outcomes: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    highlight: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class PortfolioSkill(Base):
    """Legacy m2m kept around for future scoring use. Not populated in Phase 3."""

    __tablename__ = "portfolio_skills"

    portfolio_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=1)
