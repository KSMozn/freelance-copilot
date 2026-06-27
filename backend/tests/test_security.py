from uuid import uuid4

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_round_trip() -> None:
    raw = "correct horse battery staple"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed)
    assert not verify_password("wrong", hashed)


def test_access_and_refresh_tokens_round_trip() -> None:
    uid = uuid4()
    access = create_access_token(uid)
    refresh = create_refresh_token(uid)
    assert decode_token(access, "access")["sub"] == str(uid)
    assert decode_token(refresh, "refresh")["sub"] == str(uid)


def test_token_type_is_enforced() -> None:
    import jwt as _jwt

    access = create_access_token(uuid4())
    try:
        decode_token(access, "refresh")
    except _jwt.InvalidTokenError:
        return
    raise AssertionError("access token should not validate as refresh")
