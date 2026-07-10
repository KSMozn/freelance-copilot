from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.refresh_token import RefreshTokenRecord
from app.infrastructure.db.models.refresh_token import RefreshToken


def _to_domain(row: RefreshToken) -> RefreshTokenRecord:
    return RefreshTokenRecord(
        id=row.id,
        family_id=row.family_id,
        principal_type=row.principal_type,
        subject_id=row.subject_id,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        revoked_reason=row.revoked_reason,
        created_at=row.created_at,
    )


class SQLAlchemyRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        jti: UUID,
        family_id: UUID,
        principal_type: str,
        subject_id: UUID,
        expires_at: datetime,
    ) -> None:
        self._session.add(
            RefreshToken(
                id=jti,
                family_id=family_id,
                principal_type=principal_type,
                subject_id=subject_id,
                expires_at=expires_at,
            )
        )
        await self._session.commit()

    async def get(self, jti: UUID) -> RefreshTokenRecord | None:
        row = await self._session.get(RefreshToken, jti)
        return _to_domain(row) if row is not None else None

    async def revoke(self, jti: UUID, *, reason: str, at: datetime) -> None:
        """Revoke a single token — but only if it is still live, so a logout
        can't overwrite an earlier `rotated`/`reuse_detected` reason."""
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.id == jti)
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=at, revoked_reason=reason)
        )
        await self._session.commit()

    async def revoke_family(
        self, family_id: UUID, *, reason: str, at: datetime
    ) -> None:
        """Revoke every still-live token in a family (logout / reuse)."""
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id)
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=at, revoked_reason=reason)
        )
        await self._session.commit()

    async def revoke_all_for_subject(
        self, principal_type: str, subject_id: UUID, *, reason: str, at: datetime
    ) -> None:
        """Revoke every still-live token a principal holds, across all
        families (password reset / account-wide sign-out)."""
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.principal_type == principal_type)
            .where(RefreshToken.subject_id == subject_id)
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=at, revoked_reason=reason)
        )
        await self._session.commit()
