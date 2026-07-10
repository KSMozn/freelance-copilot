from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any, Literal
from uuid import UUID

import jwt
from passlib.context import CryptContext  # type: ignore[import-untyped]  # passlib ships no stubs

from app.core.config import get_settings

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]
PrincipalType = Literal["user", "admin"]


def hash_password(password: str) -> str:
    # CryptContext is untyped (passlib has no stubs); hash() returns str at runtime.
    hashed: str = _pwd_ctx.hash(password)
    return hashed


def verify_password(password: str, hashed: str) -> bool:
    # CryptContext is untyped (passlib has no stubs); verify() returns bool at runtime.
    ok: bool = _pwd_ctx.verify(password, hashed)
    return ok


@lru_cache(maxsize=1)
def _dummy_password_hash() -> str:
    # Hashed through the same context as real passwords so the cost matches
    # whatever bcrypt work factor is configured.
    return hash_password("timing-equalization-dummy")


def dummy_verify_password() -> None:
    """Burn one bcrypt verification against a throwaway hash.

    Called on the login path when the account lookup misses (unknown email or
    passwordless OTP-only account) so the rejection costs the same as a real
    wrong-password check — response timing can't enumerate registered emails.
    """
    verify_password("not-the-dummy-password", _dummy_password_hash())


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    principal_type: PrincipalType,
    extra: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        # `pt` distinguishes admin JWTs from user JWTs — the two token
        # spaces are strictly separate (an admin JWT can't be used on
        # /students, a user JWT can't be used on /admin).
        "pt": principal_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(
    subject: str | UUID, principal_type: PrincipalType = "user"
) -> str:
    settings = get_settings()
    return _create_token(
        str(subject),
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
        principal_type,
    )


def create_impersonation_token(
    subject: str | UUID,
    *,
    actor_admin_id: str | UUID,
    actor_email: str,
) -> str:
    """Mint a short-lived, non-refreshable access token for admin "view as user".

    Carries an `act` (actor) claim identifying the impersonating admin and an
    `imp` flag so an impersonated session is distinguishable from the user's own
    login in logs. It is an ordinary `pt=user` access token otherwise (the admin
    is acting *as* the user), but with a shortened TTL and no paired refresh
    token, so the session self-expires instead of lasting 14 days.
    """
    settings = get_settings()
    return _create_token(
        str(subject),
        "access",
        timedelta(minutes=settings.impersonation_token_expire_minutes),
        "user",
        extra={
            "imp": True,
            "act": {"aid": str(actor_admin_id), "email": actor_email},
        },
    )


def create_refresh_token(
    subject: str | UUID,
    principal_type: PrincipalType = "user",
    *,
    jti: str | None = None,
    family_id: str | None = None,
) -> str:
    """Mint a refresh token.

    When `jti`/`family_id` are supplied they are embedded so the token can be
    tracked server-side for rotation + reuse detection. Omitting them (e.g.
    admin impersonation) yields an untracked token that the refresh flow
    treats as legacy and bootstraps into a tracked family on first use.
    """
    settings = get_settings()
    extra: dict[str, Any] = {}
    if jti is not None:
        extra["jti"] = jti
    if family_id is not None:
        extra["fid"] = family_id
    return _create_token(
        str(subject),
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
        principal_type,
        extra=extra or None,
    )


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"expected {expected_type} token")
    # Legacy tokens without `pt` default to "user" for backwards compat.
    payload.setdefault("pt", "user")
    return payload
