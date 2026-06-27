from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import ARRAY, Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, TimestampMixin, UUIDPKMixin


class Portfolio(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "portfolios"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    github_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    live_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_domains: Mapped[list[str]] = mapped_column(
        ARRAY(String(120)), nullable=False, default=list
    )
    features: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    highlight: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class PortfolioSkill(Base):
    __tablename__ = "portfolio_skills"

    portfolio_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=1)
