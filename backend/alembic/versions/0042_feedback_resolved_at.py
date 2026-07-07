"""Feedback triage — resolved_at on feedback_entries.

Admin inbox needs a way to mark a feedback item as handled. Nullable
timestamp so `NULL` means "still needs attention" (the default state
for both existing rows and new submissions) and a value means
"resolved at this time by an admin." The resolving admin's id/email
lands in the row's existing `meta` JSONB — no FK needed.
"""

import sqlalchemy as sa

from alembic import op

revision = "0042_feedback_resolved_at"
down_revision = "0041_coach_internship_usage_kind"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "feedback_entries",
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_feedback_resolved_at",
        "feedback_entries",
        ["resolved_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_feedback_resolved_at", table_name="feedback_entries")
    op.drop_column("feedback_entries", "resolved_at")
