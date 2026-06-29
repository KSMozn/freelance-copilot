"""phase 16: Mermaid diagrams on proposals

Adds `diagrams` JSONB to `proposals` — a small list of Mermaid sources
(system + sequence) the proposal can render inline to answer "how would you
build this?" without a follow-up call.

Revision ID: 0012_phase16_proposal_diagrams
Revises: 0011_phase15_implementation_plan
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012_phase16_proposal_diagrams"
down_revision = "0011_phase15_implementation_plan"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "proposals",
        sa.Column(
            "diagrams",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("proposals", "diagrams")
