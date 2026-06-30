"""phase K: add `department` to student_profiles

The Education step now splits university / department: "University of
Riyadh" + "College of Computer & Information Sciences" reads better on a
CV than one squished line. `department` is nullable — the wizard treats
it as optional and skips it on the rendered CV when empty.

Revision ID: 0029_phase_k_student_department
Revises: 0028_phase_k_student_persona
Create Date: 2026-06-30
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0029_phase_k_student_department"
down_revision = "0028_phase_k_student_persona"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_profiles",
        sa.Column("department", sa.String(length=200), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("student_profiles", "department")
