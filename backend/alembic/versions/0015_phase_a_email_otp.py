"""phase A: email-OTP signup + verification

Adds:
  * `email_otp_codes` table — hashed 6-digit codes used for passwordless
    signup / sign-in / email-change verification.
  * `users.email_verified_at` — set when an OTP is successfully consumed.
  * `users.last_login_at` — touched on every successful auth.
  * `users.password_hash` made NULLABLE — accounts created via OTP never
    set a password; password is now an optional secondary path.

Revision ID: 0015_phase_a_email_otp
Revises: 0014_phase18_company_research
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0015_phase_a_email_otp"
down_revision = "0014_phase18_company_research"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_otp_codes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "purpose",
            sa.Enum("login", "register", "email_change", name="otp_purpose"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_email_otp_codes_lookup",
        "email_otp_codes",
        ["email", "purpose", "consumed_at"],
    )
    op.create_index(
        "ix_email_otp_codes_expires_at",
        "email_otp_codes",
        ["expires_at"],
    )

    op.add_column(
        "users",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=True)


def downgrade() -> None:
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=False)
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "email_verified_at")

    op.drop_index("ix_email_otp_codes_expires_at", table_name="email_otp_codes")
    op.drop_index("ix_email_otp_codes_lookup", table_name="email_otp_codes")
    op.drop_table("email_otp_codes")
    sa.Enum(name="otp_purpose").drop(op.get_bind(), checkfirst=True)
