"""phase 6: application tracker + outcome snapshots

Extends the Phase-1 applications + application_history tables to the Phase-6
contract:

- applications: drop connects_spent, bid_amount, outcome_at; add per-status
  timestamps (viewed_at, interview_at, offer_at, won_at, rejected_at,
  withdrawn_at, completed_at), contract_amount, client_response,
  rejection_reason, portfolio_ids (jsonb), snapshot (jsonb)
- application_status enum: add 'draft' and 'offer' values
- application_history: add user_id FK, rename changed_at → created_at

Revision ID: 0006_phase6_application
Revises: 0005_phase5_proposal
Create Date: 2026-06-28
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0006_phase6_application"
down_revision = "0005_phase5_proposal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- application_status enum: add the two new values ---
    # ALTER TYPE … ADD VALUE cannot run inside a transaction; use the
    # autocommit block so Alembic commits before continuing.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'draft'")
        op.execute("ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'offer'")

    # --- applications: drop legacy columns, add Phase-6 columns ---
    op.drop_column("applications", "connects_spent")
    op.drop_column("applications", "bid_amount")
    op.drop_column("applications", "outcome_at")

    op.add_column(
        "applications", sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "applications",
        sa.Column("interview_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "applications", sa.Column("offer_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "applications", sa.Column("won_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "applications",
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "applications", sa.Column("contract_amount", sa.Numeric(12, 2), nullable=True)
    )
    op.add_column(
        "applications", sa.Column("client_response", sa.Text(), nullable=True)
    )
    op.add_column(
        "applications", sa.Column("rejection_reason", sa.Text(), nullable=True)
    )
    op.add_column(
        "applications",
        sa.Column(
            "portfolio_ids", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
    )
    op.add_column(
        "applications", sa.Column("snapshot", postgresql.JSONB(), nullable=True)
    )

    # --- application_history: add user_id, rename changed_at → created_at ---
    op.add_column(
        "application_history",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_application_history_user_id", "application_history", ["user_id"]
    )
    op.alter_column(
        "application_history",
        "changed_at",
        new_column_name="created_at",
        server_default=sa.func.now(),
    )


def downgrade() -> None:
    op.alter_column(
        "application_history",
        "created_at",
        new_column_name="changed_at",
        server_default=None,
    )
    op.drop_index("ix_application_history_user_id", table_name="application_history")
    op.drop_column("application_history", "user_id")

    op.drop_column("applications", "snapshot")
    op.drop_column("applications", "portfolio_ids")
    op.drop_column("applications", "rejection_reason")
    op.drop_column("applications", "client_response")
    op.drop_column("applications", "contract_amount")
    op.drop_column("applications", "completed_at")
    op.drop_column("applications", "withdrawn_at")
    op.drop_column("applications", "rejected_at")
    op.drop_column("applications", "won_at")
    op.drop_column("applications", "offer_at")
    op.drop_column("applications", "interview_at")
    op.drop_column("applications", "viewed_at")

    op.add_column(
        "applications", sa.Column("outcome_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "applications", sa.Column("bid_amount", sa.Numeric(12, 2), nullable=True)
    )
    op.add_column("applications", sa.Column("connects_spent", sa.Integer(), nullable=True))

    # Note: PostgreSQL has no built-in way to remove enum values without
    # rebuilding the type. Downgrade leaves 'draft' and 'offer' in place.
