"""Add `cv.docx` to usage_event_kind enum.

Emitted by the DOCX CV download endpoint. usage_event inserts silently
drop on the fire-and-forget path if the enum doesn't include the value;
the SELECT-side would also LookupError once rows exist (same pattern as
the career_pack.* fix in 0037).
"""
from alembic import op


revision = "0039_cv_docx_usage_kind"
down_revision = "0038_backfill_students"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE usage_event_kind ADD VALUE IF NOT EXISTS 'cv.docx'")


def downgrade() -> None:
    # Postgres can't remove enum values without rebuilding the type;
    # leaving it in place is harmless.
    pass
