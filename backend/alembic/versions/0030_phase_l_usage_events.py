"""phase L: usage_events table for the admin panel

Records every "meaningful" call from the app — coach calls (draft-summary,
proofread, photo review, text improve), CV renders (preview / pdf), auth
events (register / login), impersonation events. The admin activity panel
paginates over these; the overview dashboard aggregates them.

Kept intentionally narrow: user_id (nullable — some events are pre-auth
or system-issued), kind, status ("ok" / "error"), duration_ms, error
message when it failed, and a flexible `meta` JSONB for kind-specific
extras (target_user_id for impersonation, entry_kind for entry_create,
etc.). Fire-and-forget from the emit site — a slow log write can't slow
a user-facing request.

Revision ID: 0030_phase_l_usage_events
Revises: 0029_phase_k_student_department
Create Date: 2026-07-01
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0030_phase_l_usage_events"
down_revision = "0029_phase_k_student_department"
branch_labels = None
depends_on = None


USAGE_EVENT_KINDS = (
    "auth.register",
    "auth.login",
    "auth.otp_request",
    "auth.otp_verify",
    "coach.draft_summary",
    "coach.proofread",
    "coach.photo",
    "coach.text",
    "coach.email",
    "cv.preview",
    "cv.pdf",
    "admin.impersonate",
    "admin.action",
    "error",
)

USAGE_EVENT_STATUSES = ("ok", "error")


def upgrade() -> None:
    op.create_table(
        "usage_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "kind",
            sa.Enum(*USAGE_EVENT_KINDS, name="usage_event_kind"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(*USAGE_EVENT_STATUSES, name="usage_event_status"),
            nullable=False,
        ),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "meta",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_usage_events_created_kind",
        "usage_events",
        ["created_at", "kind"],
    )
    op.create_index(
        "ix_usage_events_user_created",
        "usage_events",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_usage_events_user_created", table_name="usage_events")
    op.drop_index("ix_usage_events_created_kind", table_name="usage_events")
    op.drop_table("usage_events")
    sa.Enum(name="usage_event_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="usage_event_kind").drop(op.get_bind(), checkfirst=True)
