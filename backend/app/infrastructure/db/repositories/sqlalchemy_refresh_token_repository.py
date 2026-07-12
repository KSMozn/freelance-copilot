from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.refresh_token import RefreshTokenRecord
from app.infrastructure.db.advisory_lock import lock_principal
from app.infrastructure.db.models.admin_user import AdminUser
from app.infrastructure.db.models.refresh_token import RefreshToken
from app.infrastructure.db.models.user import User


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
    """Write methods open their own transaction (advisory lock + write must be
    atomic), so they first roll back the session's autobegun read transaction.
    Invariant: callers must have no pending uncommitted writes on the shared
    per-request session when calling in — they would be silently discarded."""

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
        expected_password_hash: str | None = None,
    ) -> bool:
        if self._session.in_transaction():
            await self._session.rollback()
        async with self._session.begin():
            await lock_principal(self._session, principal_type, subject_id)
            if expected_password_hash is not None:
                model = AdminUser if principal_type == "admin" else User
                current_hash = (
                    await self._session.execute(
                        select(model.password_hash).where(model.id == subject_id)
                    )
                ).scalar_one_or_none()
                if current_hash != expected_password_hash:
                    return False
            self._session.add(
                RefreshToken(
                    id=jti,
                    family_id=family_id,
                    principal_type=principal_type,
                    subject_id=subject_id,
                    expires_at=expires_at,
                )
            )
            return True

    async def get(self, jti: UUID) -> RefreshTokenRecord | None:
        row = await self._session.get(RefreshToken, jti)
        return _to_domain(row) if row is not None else None

    async def rotate(
        self,
        *,
        current_jti: UUID,
        new_jti: UUID,
        family_id: UUID,
        principal_type: str,
        subject_id: UUID,
        expires_at: datetime,
        at: datetime,
    ) -> bool:
        if self._session.in_transaction():
            await self._session.rollback()
        async with self._session.begin():
            await lock_principal(self._session, principal_type, subject_id)
            claimed = await self._session.execute(
                update(RefreshToken)
                .where(RefreshToken.id == current_jti)
                .where(RefreshToken.family_id == family_id)
                .where(RefreshToken.principal_type == principal_type)
                .where(RefreshToken.subject_id == subject_id)
                .where(RefreshToken.revoked_at.is_(None))
                .where(RefreshToken.expires_at > at)
                .values(revoked_at=at, revoked_reason="rotated")
                .returning(RefreshToken.id)
            )
            if claimed.scalar_one_or_none() is None:
                return False
            self._session.add(
                RefreshToken(
                    id=new_jti,
                    family_id=family_id,
                    principal_type=principal_type,
                    subject_id=subject_id,
                    expires_at=expires_at,
                )
            )
        return True

    async def revoke_family(
        self,
        family_id: UUID,
        *,
        principal_type: str,
        subject_id: UUID,
        reason: str,
        at: datetime,
    ) -> None:
        """Revoke every still-live token in a family (logout / reuse)."""
        if self._session.in_transaction():
            await self._session.rollback()
        async with self._session.begin():
            await lock_principal(self._session, principal_type, subject_id)
            await self._session.execute(
                update(RefreshToken)
                .where(RefreshToken.family_id == family_id)
                .where(RefreshToken.principal_type == principal_type)
                .where(RefreshToken.subject_id == subject_id)
                .where(RefreshToken.revoked_at.is_(None))
                .values(revoked_at=at, revoked_reason=reason)
            )

    async def revoke_all_for_subject(
        self, principal_type: str, subject_id: UUID, *, reason: str, at: datetime
    ) -> None:
        """Revoke every still-live token a principal holds, across all
        families (password reset / account-wide sign-out)."""
        if self._session.in_transaction():
            await self._session.rollback()
        async with self._session.begin():
            await lock_principal(self._session, principal_type, subject_id)
            await self._session.execute(
                update(RefreshToken)
                .where(RefreshToken.principal_type == principal_type)
                .where(RefreshToken.subject_id == subject_id)
                .where(RefreshToken.revoked_at.is_(None))
                .values(revoked_at=at, revoked_reason=reason)
            )
