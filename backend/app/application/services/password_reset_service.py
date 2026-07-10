"""Forgot/reset password over email-delivered, single-use tokens.

The raw token (secrets.token_urlsafe) only ever exists inside the reset email;
the store keeps a SHA-256 digest, so a leaked table row cannot be replayed as
a link. A successful reset burns every outstanding link for the user and
revokes all of their refresh-token sessions — the old credential and any
stolen session die together.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from app.application.services.refresh_token_manager import RefreshTokenManager
from app.core.security import hash_password
from app.domain.exceptions import EmailDeliveryError, PasswordResetInvalidError
from app.domain.providers.email_provider import EmailMessage, EmailProvider
from app.domain.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.email_normalization import normalize_email
from app.infrastructure.email.template_renderer import render

_INVALID_MESSAGE = "This reset link is invalid or has expired. Request a new one."


def _hash_token(token: str) -> str:
    # Deterministic digest so the row can be looked up by hash. Unlike OTP
    # codes (6 digits → bcrypt), the token has ~250 bits of entropy, which
    # makes offline brute-force of a plain SHA-256 digest infeasible.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class PasswordResetService:
    def __init__(
        self,
        *,
        user_repo: UserRepository,
        reset_repo: PasswordResetTokenRepository,
        refresh_tokens: RefreshTokenManager,
        email_provider: EmailProvider,
        app_name: str,
        frontend_base_url: str,
        expires_minutes: int = 30,
    ) -> None:
        self._users = user_repo
        self._resets = reset_repo
        self._refresh = refresh_tokens
        self._email = email_provider
        self._app_name = app_name
        self._frontend_base_url = frontend_base_url.rstrip("/")
        self._expires_minutes = expires_minutes

    async def request_reset(self, *, email: str) -> None:
        """Issue a reset link if the account exists; silent no-op otherwise.

        Never signals whether the email is registered — the endpoint returns
        the same generic response either way.
        """
        email = normalize_email(email)
        user = await self._users.get_by_email(email)
        if user is None or not user.is_active:
            return

        now = datetime.now(UTC)
        token = secrets.token_urlsafe(48)
        # Only the newest link should work: burn earlier outstanding ones.
        await self._resets.invalidate_active_for_user(user.id, now)
        await self._resets.create(
            user_id=user.id,
            token_hash=_hash_token(token),
            expires_at=now + timedelta(minutes=self._expires_minutes),
        )

        context = {
            "app_name": self._app_name,
            "reset_url": f"{self._frontend_base_url}/reset-password?token={token}",
            "expires_in_minutes": self._expires_minutes,
        }
        try:
            await self._email.send(
                EmailMessage(
                    to=email,
                    subject=f"Reset your {self._app_name} password",
                    html_body=render("password_reset.html", context),
                    text_body=render("password_reset.txt", context),
                    tags={"kind": "password_reset"},
                )
            )
        except Exception as exc:
            raise EmailDeliveryError(
                "We couldn't send the email right now. Please try again shortly."
            ) from exc

    async def reset_password(self, *, token: str, new_password: str) -> None:
        """Consume a reset token: set the new password and kill old sessions.

        Raises ``PasswordResetInvalidError`` (one generic message) when the
        token is unknown, already used, or expired.
        """
        record = await self._resets.get_by_token_hash(_hash_token(token.strip()))
        now = datetime.now(UTC)
        if (
            record is None
            or record.used_at is not None
            or _as_aware(record.expires_at) < now
        ):
            raise PasswordResetInvalidError(_INVALID_MESSAGE)

        user = await self._users.get_by_id(record.user_id)
        if user is None or not user.is_active:
            raise PasswordResetInvalidError(_INVALID_MESSAGE)

        await self._users.set_password(user.id, hash_password(new_password))
        # Completing a reset proves control of the inbox — same signal the
        # OTP flow uses to verify an email.
        if user.email_verified_at is None:
            await self._users.mark_email_verified(user.id, now)
        # Burn this link and any other outstanding one.
        await self._resets.invalidate_active_for_user(user.id, now)
        # Old refresh tokens must not outlive the old password.
        await self._refresh.revoke_all_for(user.id, "user")


def _as_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
