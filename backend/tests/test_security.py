from uuid import uuid4

from app.core.security import (
    create_access_token,
    create_impersonation_token,
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


def test_impersonation_token_carries_actor_and_is_shorter_lived() -> None:
    target = uuid4()
    admin = uuid4()
    imp = create_impersonation_token(
        target, actor_admin_id=admin, actor_email="root@example.com"
    )
    normal = create_access_token(target)

    imp_data = decode_token(imp, "access")
    normal_data = decode_token(normal, "access")

    # It's a user token acting as the target, flagged as impersonation, and
    # names the acting admin so logs can tell it apart from a real login.
    assert imp_data["sub"] == str(target)
    assert imp_data["pt"] == "user"
    assert imp_data["imp"] is True
    assert imp_data["act"] == {"aid": str(admin), "email": "root@example.com"}
    # And it expires sooner than a normal 60-min access token (default 30 min).
    assert imp_data["exp"] < normal_data["exp"]
