"""Refresh-token rotation with reuse detection.

Shared by the user and admin auth services. Every refresh rotates: the
presented token is revoked and a fresh one is issued in the same family. If an
already-rotated token is replayed later, that's a theft signal — the whole
family is revoked so both the attacker's and the victim's sessions die and a
re-login is forced.

Access tokens stay stateless (short-lived); only refresh tokens are tracked.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token
from app.domain.exceptions import InvalidCredentialsError
from app.infrastructure.db.repositories.sqlalchemy_refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)

# A legit client can fire two refreshes almost simultaneously (double-submit,
# retry). Within this window we reject the duplicate WITHOUT nuking the family;
# a replay after it is treated as theft.
_REUSE_GRACE_SECONDS = 15


class RefreshTokenManager:
    def __init__(self, repo: SQLAlchemyRefreshTokenRepository) -> None:
        self._repo = repo
        self._ttl_days = get_settings().refresh_token_expire_days

    def _expiry(self, now: datetime) -> datetime:
        return now + timedelta(days=self._ttl_days)

    async def issue(
        self, subject_id: UUID, principal_type: str
    ) -> tuple[str, str]:
        """Mint a fresh (access, refresh) pair in a brand-new family."""
        now = datetime.now(UTC)
        family_id = uuid4()
        jti = uuid4()
        await self._repo.create(
            jti=jti,
            family_id=family_id,
            principal_type=principal_type,
            subject_id=subject_id,
            expires_at=self._expiry(now),
        )
        return (
            create_access_token(subject_id, principal_type=principal_type),  # type: ignore[arg-type]
            create_refresh_token(
                subject_id,
                principal_type=principal_type,  # type: ignore[arg-type]
                jti=str(jti),
                family_id=str(family_id),
            ),
        )

    async def rotate(
        self, data: dict[str, Any], principal_type: str, subject_id: UUID
    ) -> tuple[str, str]:
        """Validate the presented refresh token and rotate it.

        `data` is the already signature-verified JWT payload. Raises
        InvalidCredentialsError on any reuse/expiry/unknown-token condition.
        """
        now = datetime.now(UTC)
        jti_claim = data.get("jti")
        fid_claim = data.get("fid")

        # Legacy token (minted before this feature) or an impersonation token:
        # no jti to check against the store — bootstrap into a tracked family.
        if not jti_claim or not fid_claim:
            return await self.issue(subject_id, principal_type)

        row = await self._repo.get(UUID(str(jti_claim)))
        if row is None:
            # Claimed a jti we never issued (forged, or pruned) — reject.
            raise InvalidCredentialsError("Refresh token not recognized")

        if row.revoked_at is not None:
            already_rotated = row.revoked_reason == "rotated"
            past_grace = (now - row.revoked_at).total_seconds() > _REUSE_GRACE_SECONDS
            if already_rotated and past_grace:
                # A rotated token resurfacing well after rotation == theft.
                await self._repo.revoke_family(
                    row.family_id, reason="reuse_detected", at=now
                )
            raise InvalidCredentialsError("Refresh token already used")

        if row.expires_at <= now:
            raise InvalidCredentialsError("Refresh token expired")

        # Valid — revoke the presented token and issue its successor.
        await self._repo.revoke(row.id, reason="rotated", at=now)
        new_jti = uuid4()
        await self._repo.create(
            jti=new_jti,
            family_id=row.family_id,
            principal_type=principal_type,
            subject_id=subject_id,
            expires_at=self._expiry(now),
        )
        return (
            create_access_token(subject_id, principal_type=principal_type),  # type: ignore[arg-type]
            create_refresh_token(
                subject_id,
                principal_type=principal_type,  # type: ignore[arg-type]
                jti=str(new_jti),
                family_id=str(row.family_id),
            ),
        )

    async def revoke_all_for(
        self, subject_id: UUID, principal_type: str, *, reason: str = "password_reset"
    ) -> None:
        """Revoke every live session a principal holds, across all families.

        Used after a password reset so stolen/old refresh tokens die with the
        old credential.
        """
        await self._repo.revoke_all_for_subject(
            principal_type, subject_id, reason=reason, at=datetime.now(UTC)
        )

    async def revoke_session(self, data: dict[str, Any]) -> None:
        """Logout: revoke the whole family behind the presented refresh token.

        Idempotent and non-leaking — an unknown/legacy token is a no-op
        (the client drops it), never an error.
        """
        now = datetime.now(UTC)
        fid_claim = data.get("fid")
        jti_claim = data.get("jti")
        if fid_claim:
            await self._repo.revoke_family(
                UUID(str(fid_claim)), reason="logout", at=now
            )
        elif jti_claim:
            await self._repo.revoke(UUID(str(jti_claim)), reason="logout", at=now)
