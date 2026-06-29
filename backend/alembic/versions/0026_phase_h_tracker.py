"""phase H: application tracker extensions

Three child tables hanging off `applications`:

  * `recruiter_interactions` — every back-and-forth with the recruiter
    (channel + direction + occurred_at + summary + raw content).
  * `interview_events` — each scheduled interview round with its format,
    notes, my-feedback, and outcome.
  * `follow_up_reminders` — a personal to-do list per application; the
    UI surfaces overdue + due-soon items on the dashboard.

Plus two FK columns on `applications`:
  * `resume_output_id` — the exact tailored resume sent.
  * `cover_letter_output_id` — the exact cover letter sent.

Both reference the Phase F `outputs` table so "which version did I send?"
is one read away.

Revision ID: 0026_phase_h_tracker
Revises: 0025_phase_f_outputs
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0026_phase_h_tracker"
down_revision = "0025_phase_f_outputs"
branch_labels = None
depends_on = None


INTERACTION_CHANNELS = ("email", "linkedin", "phone", "in_person", "other")
INTERACTION_DIRECTIONS = ("inbound", "outbound")
INTERVIEW_FORMATS = (
    "phone_screen",
    "technical",
    "system_design",
    "behavioral",
    "onsite",
    "final",
    "other",
)
INTERVIEW_OUTCOMES = ("pending", "pass", "fail", "cancelled")


def upgrade() -> None:
    # ---- applications: link to the exact outputs sent --------------------
    op.add_column(
        "applications",
        sa.Column(
            "resume_output_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("outputs.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "applications",
        sa.Column(
            "cover_letter_output_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("outputs.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    op.create_table(
        "recruiter_interactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "channel",
            sa.Enum(*INTERACTION_CHANNELS, name="interaction_channel"),
            nullable=False,
            server_default="email",
        ),
        sa.Column(
            "direction",
            sa.Enum(*INTERACTION_DIRECTIONS, name="interaction_direction"),
            nullable=False,
        ),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("contact_name", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "interview_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("round_label", sa.String(length=120), nullable=False),
        sa.Column(
            "format",
            sa.Enum(*INTERVIEW_FORMATS, name="interview_format"),
            nullable=False,
            server_default="phone_screen",
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.SmallInteger(), nullable=True),
        sa.Column("interviewer_names", sa.Text(), nullable=True),
        sa.Column("interviewer_notes", sa.Text(), nullable=True),
        sa.Column("my_feedback", sa.Text(), nullable=True),
        sa.Column(
            "outcome",
            sa.Enum(*INTERVIEW_OUTCOMES, name="interview_outcome"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    op.create_table(
        "follow_up_reminders",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "channel",
            sa.Enum(
                *INTERACTION_CHANNELS, name="interaction_channel", create_type=False
            ),
            nullable=True,
        ),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_follow_up_reminders_user_open",
        "follow_up_reminders",
        ["user_id", "due_at"],
        postgresql_where=sa.text("completed_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_follow_up_reminders_user_open", table_name="follow_up_reminders"
    )
    op.drop_table("follow_up_reminders")
    op.drop_table("interview_events")
    sa.Enum(name="interview_outcome").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="interview_format").drop(op.get_bind(), checkfirst=True)
    op.drop_table("recruiter_interactions")
    sa.Enum(name="interaction_direction").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="interaction_channel").drop(op.get_bind(), checkfirst=True)

    op.drop_column("applications", "cover_letter_output_id")
    op.drop_column("applications", "resume_output_id")
