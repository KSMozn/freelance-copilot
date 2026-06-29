"""phase F: unified outputs table + citations

`outputs` subsumes "generated artifact" across formats — cover letters,
Upwork proposals, recruiter replies, LinkedIn messages, consulting
proposals, screening answers, tailored resumes. One row per generation.
The existing `proposals` table stays in place for backwards compat;
phase F adds a sibling table rather than migrating in-place so callers
already shipped against `/proposals` keep working unchanged.

Every row carries the markdown + html body and a JSONB `citations` array
of ``{claim, evidence_type, evidence_id, snippet}`` rows pointing back
into the knowledge graph (experiences / projects / repositories /
certificates / content_items).

Revision ID: 0025_phase_f_outputs
Revises: 0024_phase_e_match_reports
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0025_phase_f_outputs"
down_revision = "0024_phase_e_match_reports"
branch_labels = None
depends_on = None


OUTPUT_KINDS = (
    "upwork_proposal",
    "cover_letter",
    "recruiter_reply",
    "linkedin_message",
    "consulting_proposal",
    "screening_answer",
    "resume_tailored",
)


def upgrade() -> None:
    op.create_table(
        "outputs",
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
            "persona_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("personas.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "kind",
            sa.Enum(*OUTPUT_KINDS, name="output_kind"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("content_html", sa.Text(), nullable=True),
        sa.Column(
            "citations",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("tone", sa.String(length=40), nullable=True),
        sa.Column("ai_provider", sa.String(length=64), nullable=True),
        sa.Column("ai_model", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_outputs_user_job", "outputs", ["user_id", "job_id"])
    op.create_index(
        "ix_outputs_user_kind_created", "outputs", ["user_id", "kind", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_outputs_user_kind_created", table_name="outputs")
    op.drop_index("ix_outputs_user_job", table_name="outputs")
    op.drop_table("outputs")
    sa.Enum(name="output_kind").drop(op.get_bind(), checkfirst=True)
