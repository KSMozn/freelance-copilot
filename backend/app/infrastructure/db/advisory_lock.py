from __future__ import annotations

import hashlib
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def principal_lock_key(principal_type: str, subject_id: UUID) -> int:
    digest = hashlib.sha256(f"{principal_type}:{subject_id}".encode()).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=True)


async def lock_principal(session: AsyncSession, principal_type: str, subject_id: UUID) -> None:
    await session.execute(
        text("SELECT pg_advisory_xact_lock(:key)"),
        {"key": principal_lock_key(principal_type, subject_id)},
    )
