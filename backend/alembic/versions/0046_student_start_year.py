"""Education start year — add `start_year` to student_profiles.

Optional. Pairs with `graduation_year` so a student can show their full
study period (e.g. 2023–2027) on the CV. Nullable; NULL = not provided,
the default for every existing row and every profile that omits it.

Revision ID: 0046_student_start_year
Revises: 0045_feedback_screenshot
Create Date: 2026-07-19
"""

import sqlalchemy as sa

from alembic import op

revision = "0046_student_start_year"
down_revision = "0045_feedback_screenshot"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_profiles",
        sa.Column("start_year", sa.SmallInteger(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("student_profiles", "start_year")
