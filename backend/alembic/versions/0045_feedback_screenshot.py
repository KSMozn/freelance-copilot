"""Feedback screenshots — screenshot_file_id on feedback_entries.

Students can optionally attach a screenshot to general feedback so a bug
report can carry visual context. The image itself lives in the shared
`uploaded_files` registry (same store as profile photos); this nullable
FK points at it. `ON DELETE SET NULL` so pruning an uploaded file never
deletes the feedback row — the message is the record of value, the
screenshot is a bonus. NULL = no screenshot, the default for every
existing row and every message-only submission.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0045_feedback_screenshot"
down_revision = "0044_password_reset_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "feedback_entries",
        sa.Column("screenshot_file_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_feedback_screenshot_file_id_uploaded_files",
        "feedback_entries",
        "uploaded_files",
        ["screenshot_file_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_feedback_screenshot_file_id_uploaded_files",
        "feedback_entries",
        type_="foreignkey",
    )
    op.drop_column("feedback_entries", "screenshot_file_id")
