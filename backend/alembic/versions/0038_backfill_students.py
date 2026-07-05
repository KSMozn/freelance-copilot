"""Backfill: mark all legacy accounts as students

Careero currently ships a student-only shell. Historically the register
DTO defaulted `persona_kind` to "professional", so any account created
via a code path that didn't explicitly set "student" (login-page OTP
verify, seed data, admin creation) ended up flagged professional even
though the user went through the CV wizard.

This migration flips every existing user to `selected_persona_kind =
'student'`. The default has also been changed in the DTO so new
accounts land as students by default.

Reversible: the downgrade is a no-op — there's no way to reconstruct
the original persona per user, and reverting everyone to professional
would be even less accurate.
"""
from alembic import op


revision = "0038_backfill_students"
down_revision = "0037_career_pack_usage_kinds"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE users SET selected_persona_kind = 'student' "
        "WHERE selected_persona_kind <> 'student'"
    )


def downgrade() -> None:
    # No safe reverse — original persona per user isn't recoverable.
    pass
