"""phase 15: week-by-week implementation plan on proposals

Adds `implementation_plan` JSONB to `proposals` — a calendar-shaped artifact
("Week 1: Authentication / Week 2: Billing / …") that complements the
existing per-milestone payment chunks. The fields are decoupled because
milestones drive Upwork payment scheduling while the plan exists purely for
the client-facing "how will you spend my time" narrative.

Revision ID: 0011_phase15_implementation_plan
Revises: 0010_phase14_repo_star_story
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0011_phase15_implementation_plan"
down_revision = "0010_phase14_repo_star_story"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "proposals",
        sa.Column(
            "implementation_plan",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("proposals", "implementation_plan")
