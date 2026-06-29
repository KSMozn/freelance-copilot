"""phase C: backfill a "Primary" persona for every existing user

Every existing user gets one `personas` row keyed to the `senior_engineer`
archetype, marked `is_default = true`. New OTP-verified accounts (Phase A)
will get their Primary persona through ``PersonaService.ensure_primary``
called from ``AuthService.verify_otp`` — this migration only handles the
already-present users.

Idempotent: re-running is a no-op for users who already have a default.

Revision ID: 0022_phase_c_backfill_primary
Revises: 0021_phase_c_seed_archetypes
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0022_phase_c_backfill_primary"
down_revision = "0021_phase_c_seed_archetypes"
branch_labels = None
depends_on = None


PRIMARY_ARCHETYPE_SLUG = "senior_engineer"


def upgrade() -> None:
    conn = op.get_bind()
    archetype = conn.execute(
        sa.text("SELECT id FROM persona_archetypes WHERE slug = :slug"),
        {"slug": PRIMARY_ARCHETYPE_SLUG},
    ).fetchone()
    if archetype is None:
        raise RuntimeError(
            f"Primary archetype '{PRIMARY_ARCHETYPE_SLUG}' not seeded — "
            "did 0021 run successfully?"
        )
    archetype_id = archetype[0]

    users_without_default = conn.execute(
        sa.text(
            """
            SELECT u.id FROM users u
            WHERE NOT EXISTS (
                SELECT 1 FROM personas p
                WHERE p.user_id = u.id AND p.is_default = true
            )
            """
        )
    ).fetchall()

    inserted = 0
    insert = sa.text(
        """
        INSERT INTO personas (user_id, archetype_id, name, is_default)
        VALUES (CAST(:user_id AS uuid), CAST(:archetype_id AS uuid), 'Primary', true)
        ON CONFLICT (user_id, name) DO NOTHING
        """
    )
    for (user_id,) in users_without_default:
        result = conn.execute(
            insert, {"user_id": str(user_id), "archetype_id": str(archetype_id)}
        )
        if result.rowcount:
            inserted += 1
    print(f"[phase C backfill] created Primary persona for {inserted} users")


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM personas WHERE name = 'Primary' AND is_default = true")
    )
