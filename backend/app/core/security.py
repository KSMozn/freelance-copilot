from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]
PrincipalType = Literal["user", "admin"]


def hash_password(password: str) -> str:
    return _pwd_ctx.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return _pwd_ctx.verify(password, hashed)


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
