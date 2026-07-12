"""Forgot/reset password over email-delivered, single-use tokens.

The raw token (secrets.token_urlsafe) only ever exists inside the reset email;
the store keeps a SHA-256 digest, so a leaked table row cannot be replayed as
a link. A successful reset burns every outstanding link for the user and
revokes all of their refresh-token sessions — the old credential and any
stolen session die together.

Issuance holds no database state across the provider call: the token row is
committed in its own short transaction, the email round-trips with no
connection or lock parked, and only then are strictly-older active links
burned — a commutative step, so overlapping requests always leave the newest
created-and-delivered link active regardless of completion order. A failed
send deletes the undelivered row, keeping an older delivered link usable
through a provider outage.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from app.core.security import hash_password
from app.domain.exceptions import EmailDeliveryError, PasswordResetInvalidError
from app.domain.providers.email_provider import EmailMessage, EmailProvider
from app.domain.repositories.password_reset_token_repository import (
    PasswordResetCommitter,
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
        reset_committer: PasswordResetCommitter,
        email_provider: EmailProvider,
        app_name: str,
        frontend_base_url: str,
        expires_minutes: int = 30,
    ) -> None:
        self._users = user_repo
        self._resets = reset_repo
        self._committer = reset_committer
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
        # Committed before the provider call — no transaction, connection, or
        # advisory lock survives into the email round-trip (which can block
        # for the provider's full timeout).
        record = await self._resets.create(
            user_id=user.id,
            token_hash=_hash_token(token),
            expires_at=now + timedelta(minutes=self._expires_minutes),
        )

        context = {
            "app_name": self._app_name,
            "reset_url": f"{self._frontend_base_url}/reset-password#token={token}",
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
            # The link never reached an inbox: remove it so an older delivered
            # link keeps working through a provider outage.
            await self._resets.delete(record.id)
            raise EmailDeliveryError(
                "We couldn't send the email right now. Please try again shortly."
            ) from exc
        # Only the newest delivered link should work. Burning strictly-older
        # actives after delivery is commutative across overlapping requests:
        # this token can only be burned by a yet-newer one, so out-of-order
        # completion never kills every delivered link.
        await self._resets.invalidate_older_active_for_user(user.id, record.id, now)

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

        consumed = await self._committer.consume(
            token_id=record.id,
            user_id=record.user_id,
            password_hash=hash_password(new_password),
            at=now,
        )
        if not consumed:
            raise PasswordResetInvalidError(_INVALID_MESSAGE)


def _as_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
