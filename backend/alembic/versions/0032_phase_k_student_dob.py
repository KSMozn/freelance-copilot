"""phase K: add `date_of_birth` to student_profiles

Optional. Not rendered on the CV by default (many jurisdictions treat
age as a bias risk in hiring). Captured for admin visibility and future
age-gated features.

Revision ID: 0032_phase_k_student_dob
Revises: 0031_phase_l_admin_users
Create Date: 2026-07-01
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0032_phase_k_student_dob"
down_revision = "0031_phase_l_admin_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_profiles",
        sa.Column("date_of_birth", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("student_profiles", "date_of_birth")
