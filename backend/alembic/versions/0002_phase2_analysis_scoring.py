"""phase 2: extend job_analyses + add opportunity_scores

Revision ID: 0002_phase2_analysis_scoring
Revises: 0001_initial
Create Date: 2026-06-28
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0002_phase2_analysis_scoring"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend job_analyses with the Phase-2 structured fields
    op.add_column("job_analyses", sa.Column("budget_assessment", sa.String(20), nullable=True))
    op.add_column("job_analyses", sa.Column("client_intent", sa.Text(), nullable=True))
    op.add_column("job_analyses", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column(
        "job_analyses",
        sa.Column("risks", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "job_analyses",
        sa.Column("red_flags", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "job_analyses",
        sa.Column("green_flags", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "job_analyses",
        sa.Column("questions_to_ask_client", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column("job_analyses", sa.Column("prompt_version", sa.String(40), nullable=True))

    # Opportunity scores live in their own table so we can re-score without re-analyzing
    op.create_table(
        "opportunity_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("recommendation", sa.String(20), nullable=False),
        sa.Column("confidence", sa.String(20), nullable=False),
        sa.Column("score_breakdown", postgresql.JSONB(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False, server_default=""),
        sa.Column("profile_version", sa.String(40), nullable=False, server_default="default"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("job_id", name="uq_opportunity_scores_job_id"),
    )
    op.create_index("ix_opportunity_scores_job_id", "opportunity_scores", ["job_id"])
    op.create_index("ix_opportunity_scores_analysis_id", "opportunity_scores", ["analysis_id"])


def downgrade() -> None:
    op.drop_index("ix_opportunity_scores_analysis_id", table_name="opportunity_scores")
    op.drop_index("ix_opportunity_scores_job_id", table_name="opportunity_scores")
    op.drop_table("opportunity_scores")
    for col in (
        "prompt_version",
        "questions_to_ask_client",
        "green_flags",
        "red_flags",
        "risks",
        "summary",
        "client_intent",
        "budget_assessment",
    ):
        op.drop_column("job_analyses", col)
