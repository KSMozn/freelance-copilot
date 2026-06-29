"""phase 18: company research per job

Adds `client_research` JSONB to `jobs` — a structured summary of the client's
website / product / stack extracted via the AI provider, used to personalize
the proposal.

Revision ID: 0014_phase18_company_research
Revises: 0013_phase17_repo_path_index
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0014_phase18_company_research"
down_revision = "0013_phase17_repo_path_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("client_research", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("jobs", "client_research")
