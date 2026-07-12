from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.password_reset_token import (
    PasswordResetToken as DomainToken,
)
from app.infrastructure.db.advisory_lock import lock_principal
from app.infrastructure.db.models.password_reset_token import PasswordResetToken
from app.infrastructure.db.models.refresh_token import RefreshToken
from app.infrastructure.db.models.user import User


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
    """Issuance methods commit immediately in their own short transaction:
    the service calls them around an email-provider round-trip, and no
    connection or advisory lock may be parked for that long."""

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
        token = _to_domain(row)
        await self._session.commit()
        return token

    async def get_by_token_hash(self, token_hash: str) -> DomainToken | None:
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def delete(self, token_id: UUID) -> None:
        row = await self._session.get(PasswordResetToken, token_id)
        if row is not None:
            await self._session.delete(row)
            await self._session.commit()

    async def invalidate_older_active_for_user(
        self, user_id: UUID, newest_token_id: UUID, at: datetime
    ) -> None:
        # Strictly-older only, keyed on the newest row's server-side
        # created_at: burning older actives is commutative across overlapping
        # issuances — the newest token can only be burned by a yet-newer one,
        # so out-of-order completion never kills every delivered link. A
        # created_at tie (sub-microsecond, behind the per-account limiter)
        # leaves both links live: the safe failure mode for single-use,
        # short-lived tokens.
        newest_created_at = (
            select(PasswordResetToken.created_at)
            .where(PasswordResetToken.id == newest_token_id)
            .scalar_subquery()
        )
        await self._session.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_id)
            .where(PasswordResetToken.id != newest_token_id)
            .where(PasswordResetToken.used_at.is_(None))
            .where(PasswordResetToken.created_at < newest_created_at)
            .values(used_at=at)
        )
        await self._session.commit()

    async def consume(
        self,
        *,
        token_id: UUID,
        user_id: UUID,
        password_hash: str,
        at: datetime,
    ) -> bool:
        if self._session.in_transaction():
            await self._session.rollback()

        async with self._session.begin():
            await lock_principal(self._session, "user", user_id)
            user = (
                await self._session.execute(
                    select(User).where(User.id == user_id).with_for_update()
                )
            ).scalar_one_or_none()
            if user is None or not user.is_active:
                return False

            claimed = await self._session.execute(
                update(PasswordResetToken)
                .where(PasswordResetToken.id == token_id)
                .where(PasswordResetToken.user_id == user_id)
                .where(PasswordResetToken.used_at.is_(None))
                .where(PasswordResetToken.expires_at >= at)
                .values(used_at=at)
                .returning(PasswordResetToken.id)
            )
            if claimed.scalar_one_or_none() is None:
                return False

            user.password_hash = password_hash
            if user.email_verified_at is None:
                user.email_verified_at = at

            await self._session.execute(
                update(PasswordResetToken)
                .where(PasswordResetToken.user_id == user_id)
                .where(PasswordResetToken.used_at.is_(None))
                .values(used_at=at)
            )
            await self._session.execute(
                update(RefreshToken)
                .where(RefreshToken.principal_type == "user")
                .where(RefreshToken.subject_id == user_id)
                .where(RefreshToken.revoked_at.is_(None))
                .values(revoked_at=at, revoked_reason="password_reset")
            )
        return True
