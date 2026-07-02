"""phase N: photo pan + zoom columns on student_profiles

Three new SmallInteger columns capture the student's crop selection so
the same photo renders consistently in the wizard preview, all CV
templates, and the login picker cache:

  * photo_offset_x, photo_offset_y — 0-100 percentages fed into CSS
    `background-position`.
  * photo_zoom                     — 100-300 percentage fed into CSS
    `background-size`. 100 = fits the frame; higher = zoomed in.

All non-null with server_default so existing rows land at the natural
"center + fit" defaults automatically.

Revision ID: 0035_phase_n_photo_transform
Revises: 0034_phase_m_feedback_entries
Create Date: 2026-07-02
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0035_phase_n_photo_transform"
down_revision = "0034_phase_m_feedback_entries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_profiles",
        sa.Column(
            "photo_offset_x",
            sa.SmallInteger(),
            nullable=False,
            server_default="50",
        ),
    )
    op.add_column(
        "student_profiles",
        sa.Column(
            "photo_offset_y",
            sa.SmallInteger(),
            nullable=False,
            server_default="50",
        ),
    )
    op.add_column(
        "student_profiles",
        sa.Column(
            "photo_zoom",
            sa.SmallInteger(),
            nullable=False,
            server_default="100",
        ),
    )


def downgrade() -> None:
    op.drop_column("student_profiles", "photo_zoom")
    op.drop_column("student_profiles", "photo_offset_y")
    op.drop_column("student_profiles", "photo_offset_x")
