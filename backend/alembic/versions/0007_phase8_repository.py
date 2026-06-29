"""phase 8: scanned GitHub repositories

Adds `repositories` table for auto-scanned code projects. Distinct from
`portfolios` (manual story-telling) — these are mechanically extracted from
GitHub via the REST API + heuristics + an LLM architecture-summary pass.

Embeddings reuse the existing polymorphic `embeddings` table with
`owner_type='repository'`.

Revision ID: 0007_phase8_repository
Revises: 0006_phase6_application
Create Date: 2026-06-28
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0007_phase8_repository"
down_revision = "0006_phase6_application"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("github_url", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(120), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("default_branch", sa.String(120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("languages", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("frameworks", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("libraries", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("databases", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("authentication", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("ai_providers", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("cloud", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("ci_systems", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("test_frameworks", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("has_docker", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_ci", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_tests", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("architecture_summary", sa.Text(), nullable=True),
        sa.Column("business_domain", sa.String(120), nullable=True),
        sa.Column("strengths", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("highlights", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("readme_excerpt", sa.Text(), nullable=True),
        sa.Column("scan_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("scan_error", sa.Text(), nullable=True),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "github_url", name="uq_repositories_user_github_url"),
    )
    op.create_index("ix_repositories_user_id", "repositories", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_repositories_user_id", table_name="repositories")
    op.drop_table("repositories")
