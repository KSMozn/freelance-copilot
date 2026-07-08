from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RefreshTokenRecord:
    """Server-side record of a minted refresh token (id == JWT jti)."""

    id: UUID
    family_id: UUID
    principal_type: str
    subject_id: UUID
    expires_at: datetime
    revoked_at: datetime | None
    revoked_reason: str | None
    created_at: datetime
