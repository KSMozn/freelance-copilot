from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class UserSkill(Base):
    """The global skill "pot" per user.

    One row per (user, skill). `sources` is a JSONB provenance map:
    `{repo_ids: [...], resume_ids: [...], portfolio_ids: [...], cv_upload_ids: [...],
       linkedin_snapshot_ids: [...], manual: bool, ai_suggested: bool}`.
    `evidence_count` is denormalized for cheap sorting; truth lives in `sources`.
    """

    __tablename__ = "user_skills"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skills_user_skill"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skill_catalog.id", ondelete="RESTRICT"),
        nullable=False,
    )
    proficiency: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3)
    years_experience: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 1), nullable=True
    )
    sources: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_evidence_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
