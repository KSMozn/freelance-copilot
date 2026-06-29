"""phase 17: per-repo path index for citation

Adds `path_index` JSONB to `repositories` — a filtered slice of the repo's
file tree (up to ~300 entries) used at match time to surface "relevant files"
per matched skill, instead of just naming the repo.

Revision ID: 0013_phase17_repo_path_index
Revises: 0012_phase16_proposal_diagrams
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0013_phase17_repo_path_index"
down_revision = "0012_phase16_proposal_diagrams"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "repositories",
        sa.Column(
            "path_index",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("repositories", "path_index")
