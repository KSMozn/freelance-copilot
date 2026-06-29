"""phase 9: structured stack_requirements on job analyses

Adds `stack_requirements` JSONB column to `job_analyses` for the categorized
stack signal (Tech / Architecture / Cloud / AI / Auth / Billing / Integrations
/ DB / DevOps / Testing / Deployment / Security / Nice-to-have) with 1–5 star
importance per item.

Revision ID: 0008_phase9_stack_requirements
Revises: 0007_phase8_repository
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0008_phase9_stack_requirements"
down_revision = "0007_phase8_repository"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "job_analyses",
        sa.Column(
            "stack_requirements",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("job_analyses", "stack_requirements")
