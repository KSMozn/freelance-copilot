"""Create (or reset password for) an admin_user.

Runs as a one-shot Cloud Run job. Args via env vars so we never pass
secrets on the command line:

  ADMIN_EMAIL=…       (required)
  ADMIN_PASSWORD=…    (at least 12 characters; prompted via getpass on a TTY
                      when unset, required otherwise)
  ADMIN_FULL_NAME=…   (optional)

Idempotent — if the email already exists, we update the password_hash,
revoke its refresh sessions, and update full_name instead of raising.
"""
from __future__ import annotations

import asyncio
import getpass
import os
import sys
from datetime import UTC, datetime

from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.domain.services.email_normalization import normalize_email
from app.infrastructure.db.advisory_lock import lock_principal
from app.infrastructure.db.models.admin_user import AdminUser
from app.infrastructure.db.models.refresh_token import RefreshToken

MIN_ADMIN_PASSWORD_LENGTH = 12


def validate_admin_password(password: str) -> None:
    if len(password) < MIN_ADMIN_PASSWORD_LENGTH:
        raise ValueError(
            f"ADMIN_PASSWORD must be at least {MIN_ADMIN_PASSWORD_LENGTH} characters"
        )


async def create(email: str, password: str, full_name: str | None) -> None:
    validate_admin_password(password)
    email = normalize_email(email)
    async with AsyncSessionLocal() as session:
        existing = (
            await session.execute(select(AdminUser).where(AdminUser.email == email))
        ).scalar_one_or_none()
        if existing is not None:
            await lock_principal(session, "admin", existing.id)
            existing.password_hash = hash_password(password)
            if full_name:
                existing.full_name = full_name
            await session.execute(
                update(RefreshToken)
                .where(RefreshToken.principal_type == "admin")
                .where(RefreshToken.subject_id == existing.id)
                .where(RefreshToken.revoked_at.is_(None))
                .values(
                    revoked_at=datetime.now(UTC),
                    revoked_reason="password_reset",
                )
            )
            await session.commit()
            print(f"Updated existing admin {email}.")
            return
        row = AdminUser(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
        )
        session.add(row)
        await session.commit()
        print(f"Created admin {email}.")


def main() -> None:
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    full_name = os.environ.get("ADMIN_FULL_NAME") or None
    if not email:
        print("ADMIN_EMAIL is required", file=sys.stderr)
        sys.exit(1)
    if not password:
        if not sys.stdin.isatty():
            print(
                "ADMIN_PASSWORD is required when no interactive terminal is available",
                file=sys.stderr,
            )
            sys.exit(1)
        password = getpass.getpass("Admin password (12+ characters): ")
    if full_name is None and sys.stdin.isatty():
        full_name = input("Admin full name (optional): ").strip() or None
    try:
        asyncio.run(create(email, password, full_name))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
