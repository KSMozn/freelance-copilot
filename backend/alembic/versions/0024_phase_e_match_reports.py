"""phase E: persona-aware match reports

Persists the full per-(job, persona) match analysis so:

  * The same job can be evaluated under multiple personas (a "Tech Lead"
    lens and an "AI Engineer" lens for the same posting) and both results
    persist for side-by-side comparison.
  * Re-running is cheap — the orchestrator returns the cached row unless
    the caller asks for a fresh compute.
  * The report carries the new Phase E dimensions ``leadership_fit`` and
    ``soft_skills_fit`` (alongside the existing technical / architecture
    / domain dimensions) and an actionable ``missing_recommendations`` JSONB.

Revision ID: 0024_phase_e_match_reports
Revises: 0023_phase_d_ingestion
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0024_phase_e_match_reports"
down_revision = "0023_phase_d_ingestion"
branch_labels = None
depends_on = None


INTERVIEW_CHANCE = ("low", "medium", "high")


def upgrade() -> None:
    op.create_table(
        "match_reports",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # NULL persona_id is allowed for "user-level" reports (e.g. before
        # Phase C personas existed). Active reports use the actual persona id.
        sa.Column(
            "persona_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("personas.id", ondelete="CASCADE"),
            nullable=True,
        ),
        # Headline dimensions (0..100). NULL means "not enough signal to score."
        sa.Column("overall_match", sa.SmallInteger(), nullable=False),
        sa.Column("technical_fit", sa.SmallInteger(), nullable=False),
        sa.Column("architecture_fit", sa.SmallInteger(), nullable=False),
        sa.Column("domain_fit", sa.SmallInteger(), nullable=False),
        sa.Column("leadership_fit", sa.SmallInteger(), nullable=True),
        sa.Column("soft_skills_fit", sa.SmallInteger(), nullable=True),
        sa.Column(
            "interview_chance",
            sa.Enum(*INTERVIEW_CHANCE, name="interview_chance"),
            nullable=False,
            server_default="medium",
        ),
        # `missing_critical_skills`: array of {name, importance, status}
        # objects, copied from the evidence report at compute time so the
        # report is self-contained.
        sa.Column(
            "missing_critical_skills",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        # `missing_recommendations`: array of {skill, kind, suggestion,
        # effort_estimate, priority} — the actionable Phase E payload.
        sa.Column(
            "missing_recommendations",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "rationale",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        # Diagnostic metadata so we can re-score historical reports.
        sa.Column("profile_version", sa.String(length=120), nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        # One row per (job, persona). Re-runs UPSERT this row.
        sa.UniqueConstraint(
            "job_id", "persona_id", name="uq_match_reports_job_persona"
        ),
    )
    op.create_index(
        "ix_match_reports_user_job", "match_reports", ["user_id", "job_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_match_reports_user_job", table_name="match_reports")
    op.drop_table("match_reports")
    sa.Enum(name="interview_chance").drop(op.get_bind(), checkfirst=True)
