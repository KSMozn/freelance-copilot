"""phase M: feedback_entries table

Unified table for both /feedback page submissions (kind='general') and
post-download surveys (kind='post_download'). One migration; enum +
table + two indexes.

Revision ID: 0034_phase_m_feedback_entries
Revises: 0033_phase_l_cv_templates
Create Date: 2026-07-01
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0034_phase_m_feedback_entries"
down_revision = "0033_phase_l_cv_templates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    feedback_kind = postgresql.ENUM(
        "general", "post_download", name="feedback_kind"
    )
    feedback_kind.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "feedback_entries",
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
        ),
        sa.Column(
            "kind",
            postgresql.ENUM(
                "general",
                "post_download",
                name="feedback_kind",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("rating", sa.SmallInteger(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("template_slug", sa.String(64), nullable=True),
        sa.Column(
            "meta",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_feedback_created_at_desc",
        "feedback_entries",
        ["created_at"],
    )
    op.create_index(
        "ix_feedback_user_created",
        "feedback_entries",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_feedback_user_created", table_name="feedback_entries")
    op.drop_index("ix_feedback_created_at_desc", table_name="feedback_entries")
    op.drop_table("feedback_entries")
    postgresql.ENUM(name="feedback_kind").drop(op.get_bind(), checkfirst=True)
