from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base

SKILL_CATEGORIES = (
    "language",
    "framework",
    "tool",
    "platform",
    "database",
    "domain",
    "soft",
    "practice",
    "leadership",
)


class SkillCatalog(Base):
    """Global normalized skill master list.

    Phase B replaces the loose per-row skill strings in resumes / portfolios /
    repositories with references into this table. System-seeded rows ship in
    migration 0018; user-added free-form skills land here with
    `is_system_seeded=false`.
    """

    __tablename__ = "skill_catalog"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(
        Enum(*SKILL_CATEGORIES, name="skill_category"), nullable=False
    )
    aliases: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    is_system_seeded: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
