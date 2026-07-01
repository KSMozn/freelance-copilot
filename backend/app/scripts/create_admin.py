"""Create (or reset password for) an admin_user.

Runs as a one-shot Cloud Run job. Args via env vars so we never pass
secrets on the command line:

  ADMIN_EMAIL=…       (required)
  ADMIN_PASSWORD=…    (required)
  ADMIN_FULL_NAME=…   (optional)

Idempotent — if the email already exists, we update the password_hash
and full_name instead of raising. Handy for password resets.
"""
from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.infrastructure.db.models.admin_user import AdminUser


async def create(email: str, password: str, full_name: str | None) -> None:
    async with AsyncSessionLocal() as session:
        existing = (
            await session.execute(select(AdminUser).where(AdminUser.email == email))
        ).scalar_one_or_none()
        if existing is not None:
            existing.password_hash = hash_password(password)
            if full_name:
                existing.full_name = full_name
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
    if not email or not password:
        print("ADMIN_EMAIL and ADMIN_PASSWORD env vars are required", file=sys.stderr)
        sys.exit(1)
    asyncio.run(create(email, password, full_name))


if __name__ == "__main__":
    main()
