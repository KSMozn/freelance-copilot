"""Add `internship` to the student_entry_kind enum.

Backs the new Internships wizard step. Same shape as the other
enum-extension migrations (0037 for career_pack.*, 0039 for cv.docx).
"""
from alembic import op

revision = "0040_add_internship_entry_kind"
down_revision = "0039_cv_docx_usage_kind"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE student_entry_kind ADD VALUE IF NOT EXISTS 'internship'")


def downgrade() -> None:
    # Postgres can't remove enum values without rebuilding the type;
    # leaving it in place is harmless.
    pass
