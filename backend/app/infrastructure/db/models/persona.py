from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base

PROPOSAL_TONES = (
    "pragmatic",
    "technical_deep",
    "executive",
    "consultative",
    "empathetic",
)


class PersonaArchetype(Base):
    """System-seeded persona template (Tech Lead, IC Engineer, …).

    Immutable from user CRUD endpoints — only seeded via the Alembic
    migration. Personas instantiate from one of these and may override
    any field.
    """

    __tablename__ = "persona_archetypes"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    default_weights: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    default_skill_category_weights: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    default_proposal_tone: Mapped[str] = mapped_column(
        Enum(*PROPOSAL_TONES, name="proposal_tone", create_type=False),
        nullable=False,
        default="pragmatic",
    )
    default_target_roles: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    default_seniority_band: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Persona(Base):
    """A user's instance of an archetype, freely customizable.

    Lenses over the user's knowledge graph: filter + weight + tone the same
    underlying facts. JSONB columns hold overrides on top of archetype
    defaults (merge at read time, persona wins). `is_default` is enforced
    one-per-user via a partial unique index in migration 0020.
    """

    __tablename__ = "personas"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_personas_user_name"),
        Index("ix_personas_user_archived", "user_id", "is_archived"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    archetype_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("persona_archetypes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_seniority: Mapped[str | None] = mapped_column(String(40), nullable=True)
    weights: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    skill_category_weights: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    proposal_tone: Mapped[str | None] = mapped_column(
        Enum(*PROPOSAL_TONES, name="proposal_tone", create_type=False), nullable=True
    )
    strategic_priorities: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    pinned_experience_ids: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    pinned_project_ids: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    pinned_skill_ids: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    accent_color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
