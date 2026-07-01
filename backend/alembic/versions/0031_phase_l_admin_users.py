"""phase L: split admin identities into `admin_users`

Admin accounts are now a completely separate identity space from student
accounts. Same email can exist on both sides — `samir.k@mozn.sa` as a
student in `users` and as an admin in `admin_users` are independent
accounts with independent passwords and independent lifecycles.

JWTs carry a `principal_type` claim so the backend can tell an admin
token apart from a user token at auth time; the two token types can't
be used to access each other's resources.

The old `is_superuser` column on `users` becomes vestigial (kept for
backwards compat with any migration-time bootstrap script, but no longer
consulted by the admin gate).

Revision ID: 0031_phase_l_admin_users
Revises: 0030_phase_l_usage_events
Create Date: 2026-07-01
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0031_phase_l_admin_users"
down_revision = "0030_phase_l_usage_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Independent from users.email. Same address can exist on both
        # sides. citext for case-insensitive uniqueness (matches users).
        sa.Column(
            "email",
            postgresql.CITEXT(),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
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


def downgrade() -> None:
    op.drop_table("admin_users")
