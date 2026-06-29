"""phase 5: proposal generator

Reshapes the Phase-1 placeholder proposals table to the Phase-5 contract.

- rename provider → model_provider, model → model_name
- drop draft_body and the old numeric `score` column (replaced by the
  Phase-5 integer quality_score + structured breakdown)
- add title, short_body, structured lists (questions, milestones,
  delivery_approach, risk_notes), portfolio_ids, resume_id FK,
  quality_score + quality_breakdown + quality_warnings,
  prompt_version, raw_response

Revision ID: 0005_phase5_proposal
Revises: 0004_phase4_resume
Create Date: 2026-06-28
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_phase5_proposal"
down_revision = "0004_phase4_resume"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("proposals", "provider", new_column_name="model_provider")
    op.alter_column("proposals", "model", new_column_name="model_name")
    op.drop_column("proposals", "draft_body")
    op.drop_column("proposals", "score")

    op.add_column("proposals", sa.Column("title", sa.Text(), nullable=True))
    op.add_column("proposals", sa.Column("short_body", sa.Text(), nullable=True))
    op.add_column(
        "proposals",
        sa.Column("questions", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "proposals",
        sa.Column("milestones", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "proposals",
        sa.Column(
            "delivery_approach", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
    )
    op.add_column(
        "proposals",
        sa.Column("risk_notes", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "proposals",
        sa.Column(
            "portfolio_ids", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
    )
    op.add_column(
        "proposals",
        sa.Column(
            "resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "proposals", sa.Column("quality_score", sa.Integer(), nullable=True)
    )
    op.add_column(
        "proposals", sa.Column("quality_breakdown", postgresql.JSONB(), nullable=True)
    )
    op.add_column(
        "proposals",
        sa.Column(
            "quality_warnings", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
    )
    op.add_column(
        "proposals", sa.Column("prompt_version", sa.String(40), nullable=True)
    )
    op.add_column(
        "proposals", sa.Column("raw_response", postgresql.JSONB(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("proposals", "raw_response")
    op.drop_column("proposals", "prompt_version")
    op.drop_column("proposals", "quality_warnings")
    op.drop_column("proposals", "quality_breakdown")
    op.drop_column("proposals", "quality_score")
    op.drop_column("proposals", "resume_id")
    op.drop_column("proposals", "portfolio_ids")
    op.drop_column("proposals", "risk_notes")
    op.drop_column("proposals", "delivery_approach")
    op.drop_column("proposals", "milestones")
    op.drop_column("proposals", "questions")
    op.drop_column("proposals", "short_body")
    op.drop_column("proposals", "title")

    op.add_column(
        "proposals", sa.Column("score", sa.Numeric(5, 2), nullable=True)
    )
    op.add_column("proposals", sa.Column("draft_body", sa.Text(), nullable=True))
    op.alter_column("proposals", "model_name", new_column_name="model")
    op.alter_column("proposals", "model_provider", new_column_name="provider")
