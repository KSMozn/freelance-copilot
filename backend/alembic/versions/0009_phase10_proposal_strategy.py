"""phase 10: pre-write proposal strategy

Adds a `strategy` JSONB column to `proposals` so the generator can pick the
angle (leadership / hands_on_coding / ai / architecture / fast_delivery /
enterprise / startup_mindset) BEFORE writing the body, and we can render the
choice (with rationale + emphasis points) on the Job Detail card.

Revision ID: 0009_phase10_proposal_strategy
Revises: 0008_phase9_stack_requirements
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009_phase10_proposal_strategy"
down_revision = "0008_phase9_stack_requirements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "proposals",
        sa.Column("strategy", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("proposals", "strategy")
