"""Refresh-token store for rotation + reuse detection.

One row per minted refresh token (`id` == JWT `jti`). `family_id` links a
rotation chain so replaying an already-rotated token can revoke the whole
lineage. Existing refresh tokens minted before this table have no `jti` claim
and are treated as legacy — the refresh flow bootstraps them into a new family
on first use, so this migration needs no backfill.
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from alembic import op

revision = "0043_refresh_tokens"
down_revision = "0042_feedback_resolved_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
        sa.Column("family_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column("principal_type", sa.String(length=16), nullable=False),
        sa.Column("subject_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"]
    )
    op.create_index(
        "ix_refresh_tokens_subject_id", "refresh_tokens", ["subject_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_subject_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
