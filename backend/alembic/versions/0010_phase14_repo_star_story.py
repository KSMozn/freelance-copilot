"""phase 14: STAR story per scanned repository

Adds `star_story` JSONB to `repositories` so each repo can carry one
interview-ready Situation / Task / Action / Result story plus a short
`headline` hook for proposals. Generated on-demand via the AI provider.

Revision ID: 0010_phase14_repo_star_story
Revises: 0009_phase10_proposal_strategy
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0010_phase14_repo_star_story"
down_revision = "0009_phase10_proposal_strategy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "repositories",
        sa.Column("star_story", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("repositories", "star_story")
