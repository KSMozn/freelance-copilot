"""phase B: normalized skill catalog + per-user skill "pot"

Two new tables that replace the loose JSONB skill strings scattered across
resumes / portfolios / repositories with a single source of truth:

  * `skill_catalog` — global, normalized skill master list (slug + name +
    category + aliases). System-seeded with common technologies; user-added
    free-form skills are also stored here (with `is_system_seeded = false`).
  * `user_skills` — the "pot": one row per (user, skill) with proficiency,
    sources provenance (which repos / resumes / portfolios / CVs / manual
    entries / AI suggestions contributed evidence), and evidence count.

The legacy `skills` / `resume_skills` / `portfolio_skills` tables stay in
place for now; a later phase migrates and drops them.

Revision ID: 0016_phase_b_catalog_and_pot
Revises: 0015_phase_a_email_otp
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0016_phase_b_catalog_and_pot"
down_revision = "0015_phase_a_email_otp"
branch_labels = None
depends_on = None


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


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "skill_catalog",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("slug", sa.String(length=120), nullable=False, unique=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "category",
            sa.Enum(*SKILL_CATEGORIES, name="skill_category"),
            nullable=False,
        ),
        sa.Column(
            "aliases",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "is_system_seeded",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_skill_catalog_aliases",
        "skill_catalog",
        ["aliases"],
        postgresql_using="gin",
    )
    # Trigram for fuzzy "find me 'postgress' → 'postgresql'" lookups
    op.create_index(
        "ix_skill_catalog_name_trgm",
        "skill_catalog",
        ["name"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )

    op.create_table(
        "user_skills",
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
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skill_catalog.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("proficiency", sa.SmallInteger(), nullable=False, server_default="3"),
        sa.Column("years_experience", sa.Numeric(4, 1), nullable=True),
        sa.Column(
            "sources",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("last_evidence_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "added_at",
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
        sa.UniqueConstraint("user_id", "skill_id", name="uq_user_skills_user_skill"),
    )
    op.create_index(
        "ix_user_skills_user_prof",
        "user_skills",
        ["user_id", sa.text("proficiency DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_user_skills_user_prof", table_name="user_skills")
    op.drop_table("user_skills")

    op.drop_index("ix_skill_catalog_name_trgm", table_name="skill_catalog")
    op.drop_index("ix_skill_catalog_aliases", table_name="skill_catalog")
    op.drop_table("skill_catalog")
    sa.Enum(name="skill_category").drop(op.get_bind(), checkfirst=True)
