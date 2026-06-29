"""phase 3: portfolio knowledge base

Reshapes the Phase-1 placeholder portfolios table to the Phase-3 contract:
- name → title
- description → long_description
- adds short_description, role, business_domain (singular), technologies, skills, outcomes
- drops business_domains (array form, replaced by a single canonical domain string)

Revision ID: 0003_phase3_portfolio
Revises: 0002_phase2_analysis_scoring
Create Date: 2026-06-28
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0003_phase3_portfolio"
down_revision = "0002_phase2_analysis_scoring"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("portfolios", "name", new_column_name="title")
    op.alter_column("portfolios", "description", new_column_name="long_description")

    op.add_column("portfolios", sa.Column("short_description", sa.Text(), nullable=True))
    op.add_column("portfolios", sa.Column("role", sa.String(120), nullable=True))
    op.add_column("portfolios", sa.Column("business_domain", sa.String(120), nullable=True))
    op.add_column(
        "portfolios",
        sa.Column("technologies", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "portfolios",
        sa.Column("skills", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "portfolios",
        sa.Column("outcomes", postgresql.JSONB(), nullable=False, server_default="[]"),
    )

    op.drop_column("portfolios", "business_domains")


def downgrade() -> None:
    op.add_column(
        "portfolios",
        sa.Column(
            "business_domains",
            postgresql.ARRAY(sa.String(120)),
            nullable=False,
            server_default="{}",
        ),
    )
    op.drop_column("portfolios", "outcomes")
    op.drop_column("portfolios", "skills")
    op.drop_column("portfolios", "technologies")
    op.drop_column("portfolios", "business_domain")
    op.drop_column("portfolios", "role")
    op.drop_column("portfolios", "short_description")

    op.alter_column("portfolios", "long_description", new_column_name="description")
    op.alter_column("portfolios", "title", new_column_name="name")
