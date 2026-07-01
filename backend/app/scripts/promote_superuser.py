"""Promote a user account to is_superuser=true.

Runs as a one-shot Cloud Run job (`gcloud run jobs execute
freelance-copilot-promote-superuser --update-env-vars=PROMOTE_EMAIL=…`).
Idempotent — running it twice on the same email is a no-op after the
first success.

Also handy locally:
    docker compose exec backend python -m app.scripts.promote_superuser <email>
"""
from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.infrastructure.db.models.user import User


async def promote(email: str) -> None:
    async with AsyncSessionLocal() as session:
        row = (
            await session.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if row is None:
            print(f"No user with email {email!r}", file=sys.stderr)
            sys.exit(2)
        if row.is_superuser:
            print(f"{email} is already a superuser — no-op.")
            return
        row.is_superuser = True
        await session.commit()
        print(f"Promoted {email} to superuser.")


def main() -> None:
    email = None
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = os.environ.get("PROMOTE_EMAIL")
    if not email:
        print(
            "Usage: promote_superuser <email>  (or set PROMOTE_EMAIL env)",
            file=sys.stderr,
        )
        sys.exit(1)
    asyncio.run(promote(email))


if __name__ == "__main__":
    main()
