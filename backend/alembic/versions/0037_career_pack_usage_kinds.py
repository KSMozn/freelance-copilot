"""Phase O — add career_pack.* usage_event_kind enum values

The career-pack endpoints emit `career_pack.linkedin.generate`,
`career_pack.linkedin.review`, `career_pack.github.generate`, and
`career_pack.github.review` for admin-panel visibility. usage_event
inserts were silently failing (fire-and-forget) because these values
weren't in the enum.
"""
from alembic import op


revision = "0037_career_pack_usage_kinds"
down_revision = "0036_phase_o_career_pack"
branch_labels = None
depends_on = None


_NEW_VALUES = (
    "career_pack.linkedin.generate",
    "career_pack.linkedin.review",
    "career_pack.github.generate",
    "career_pack.github.review",
)


def upgrade() -> None:
    for value in _NEW_VALUES:
        op.execute(f"ALTER TYPE usage_event_kind ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # Postgres doesn't support removing enum values without rebuilding the
    # type; leaving these in place is harmless.
    pass
