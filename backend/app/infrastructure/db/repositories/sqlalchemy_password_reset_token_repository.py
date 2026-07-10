from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.password_reset_token import (
    PasswordResetToken as DomainToken,
)
from app.infrastructure.db.models.password_reset_token import PasswordResetToken


def _to_domain(row: PasswordResetToken) -> DomainToken:
    return DomainToken(
        id=row.id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        used_at=row.used_at,
        created_at=row.created_at,
    )


class SQLAlchemyPasswordResetTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> DomainToken:
        row = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def get_by_token_hash(self, token_hash: str) -> DomainToken | None:
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def mark_used(self, token_id: UUID, used_at: datetime) -> None:
        await self._session.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.id == token_id)
            .where(PasswordResetToken.used_at.is_(None))
            .values(used_at=used_at)
        )
        await self._session.commit()

    async def invalidate_active_for_user(self, user_id: UUID, at: datetime) -> None:
        """Kill every outstanding link for a user — only the newest email's
        link should ever work, and a successful reset burns the rest."""
        await self._session.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_id)
            .where(PasswordResetToken.used_at.is_(None))
            .values(used_at=at)
        )
        await self._session.commit()
