"""phase C: persona archetypes + per-user personas

Personas are *lenses* over the user's knowledge graph (Phase B). Each user
has one or more personas, each instantiated from a system-seeded archetype
(Tech Lead, IC Engineer, Eng Manager, …) and freely customizable:
target_role, weights, skill-category emphasis, proposal tone, pinned
experiences / projects / skills.

This migration creates the two tables; the seed and backfill are split into
0021 + 0022 so each is small and idempotent.

Revision ID: 0020_phase_c_personas
Revises: 0019_phase_b_backfill
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0020_phase_c_personas"
down_revision = "0019_phase_b_backfill"
branch_labels = None
depends_on = None


PROPOSAL_TONES = (
    "pragmatic",
    "technical_deep",
    "executive",
    "consultative",
    "empathetic",
)


def upgrade() -> None:
    op.create_table(
        "persona_archetypes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("slug", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "default_weights",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "default_skill_category_weights",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "default_proposal_tone",
            sa.Enum(*PROPOSAL_TONES, name="proposal_tone"),
            nullable=False,
            server_default="pragmatic",
        ),
        sa.Column(
            "default_target_roles",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("default_seniority_band", sa.String(length=40), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "sort_order", sa.SmallInteger(), nullable=False, server_default="0"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "personas",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "archetype_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("persona_archetypes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("target_role", sa.String(length=255), nullable=True),
        sa.Column("target_seniority", sa.String(length=40), nullable=True),
        # Overrides on top of archetype defaults. Merge at read time:
        # persona.weights ∪ archetype.default_weights (persona wins).
        sa.Column(
            "weights",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "skill_category_weights",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "proposal_tone",
            sa.Enum(*PROPOSAL_TONES, name="proposal_tone", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "strategic_priorities",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "pinned_experience_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "pinned_project_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "pinned_skill_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("accent_color", sa.String(length=16), nullable=True),
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "name", name="uq_personas_user_name"),
    )
    op.create_index(
        "ix_personas_user_archived", "personas", ["user_id", "is_archived"]
    )
    # Only one default persona per user. Partial unique index keeps the
    # invariant cheap to maintain and easy to query.
    op.create_index(
        "ux_personas_one_default_per_user",
        "personas",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_default = true"),
    )


def downgrade() -> None:
    op.drop_index("ux_personas_one_default_per_user", table_name="personas")
    op.drop_index("ix_personas_user_archived", table_name="personas")
    op.drop_table("personas")
    op.drop_table("persona_archetypes")
    sa.Enum(name="proposal_tone").drop(op.get_bind(), checkfirst=True)
