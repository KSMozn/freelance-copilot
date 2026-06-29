from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from passlib.context import CryptContext

from app.domain.entities.email_otp import OtpPurpose
from app.domain.exceptions import OtpInvalidError, RateLimitedError
from app.domain.providers.email_provider import EmailMessage, EmailProvider
from app.domain.repositories.email_otp_repository import EmailOtpRepository
from app.infrastructure.email.template_renderer import render

_OTP_HASH_CTX = CryptContext(schemes=["bcrypt"], deprecated="auto")


class EmailOtpService:
    """Issue and verify 6-digit email codes.

    Codes are stored as bcrypt hashes (never plaintext). Issuance is rate-limited
    per email + purpose; verification has an attempt cap. The provider is the
    only side-effect; everything else stays in-memory / DB.
    """

    def __init__(
        self,
        *,
        otp_repo: EmailOtpRepository,
        email_provider: EmailProvider,
        app_name: str,
        from_address: str,
        expires_minutes: int = 10,
        max_attempts: int = 5,
        rate_limit_per_15min: int = 3,
    ) -> None:
        self._otps = otp_repo
        self._email = email_provider
        self._app_name = app_name
        self._from_address = from_address
        self._expires_minutes = expires_minutes
        self._max_attempts = max_attempts
        self._rate_limit = rate_limit_per_15min

    async def issue(
        self,
        *,
        email: str,
        purpose: OtpPurpose,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Generate a code, persist its hash, and email the plaintext to the user."""
        email = email.strip().lower()
        now = datetime.now(UTC)

        recent = await self._otps.count_recent_issues(
            email=email, purpose=purpose, since=now - timedelta(minutes=15)
        )
        if recent >= self._rate_limit:
            raise RateLimitedError(
                "Too many code requests. Try again in a few minutes."
            )

        code = f"{secrets.randbelow(1_000_000):06d}"
        code_hash = _OTP_HASH_CTX.hash(code)
        expires_at = now + timedelta(minutes=self._expires_minutes)

        await self._otps.create(
            email=email,
            code_hash=code_hash,
            purpose=purpose,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        context = {
            "code": code,
            "app_name": self._app_name,
            "expires_in_minutes": self._expires_minutes,
        }
        subject_label = {
            "login": "sign-in",
            "register": "sign-up",
            "email_change": "email change",
        }[purpose]
        await self._email.send(
            EmailMessage(
                to=email,
                subject=f"Your {self._app_name} {subject_label} code: {code}",
                html_body=render("otp_login.html", context),
                text_body=render("otp_login.txt", context),
                tags={"purpose": purpose, "kind": "otp"},
            )
        )

    async def verify(
        self,
        *,
        email: str,
        code: str,
        purpose: OtpPurpose,
    ) -> None:
        """Raise ``OtpInvalidError`` if the code is wrong / expired / exhausted.

        On success the code is marked consumed so it cannot be reused.
        """
        email = email.strip().lower()
        code = code.strip()

        otp = await self._otps.get_active(email=email, purpose=purpose)
        if otp is None:
            raise OtpInvalidError("No active code for this email. Request a new one.")

        now = datetime.now(UTC)
        expires_at = _as_aware(otp.expires_at)
        if expires_at < now:
            raise OtpInvalidError("This code has expired. Request a new one.")

        if otp.attempts >= self._max_attempts:
            raise OtpInvalidError(
                "Too many incorrect attempts. Request a new code."
            )

        if not _OTP_HASH_CTX.verify(code, otp.code_hash):
            await self._otps.increment_attempts(otp.id)
            raise OtpInvalidError("Incorrect code.")

        await self._otps.mark_consumed(otp.id, now)


def _as_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
