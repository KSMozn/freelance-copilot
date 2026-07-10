"""Tests for the security-hardening quick-wins."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from app.application.services.student_profile_service import _safe_filename
from app.core.config import Settings
from app.core.rate_limit import SlidingWindowLimiter
from app.infrastructure.http.url_fetcher import UrlFetchError, _assert_public_url
from app.infrastructure.storage.local_blob_store import LocalBlobStore

# ---- rate limiter ------------------------------------------------------


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = SlidingWindowLimiter(limit=3, window_s=60.0)
    for _ in range(3):
        limiter.check("k")  # first 3 allowed
    with pytest.raises(HTTPException) as exc:
        limiter.check("k")
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


def test_rate_limiter_keys_are_independent() -> None:
    limiter = SlidingWindowLimiter(limit=1, window_s=60.0)
    limiter.check("a")
    limiter.check("b")  # different key, not throttled
    with pytest.raises(HTTPException):
        limiter.check("a")


# ---- filename sanitisation --------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("photo.png", "photo.png"),
        ("../../../etc/passwd", "passwd"),
        ("..\\..\\windows\\system32", "system32"),
        ("/abs/path/x.jpg", "x.jpg"),
        ("...", "photo"),
        ("", "photo"),
        ("a b&c.png", "a_b_c.png"),
    ],
)
def test_safe_filename(raw: str, expected: str) -> None:
    out = _safe_filename(raw)
    assert "/" not in out and "\\" not in out
    assert not out.startswith(".")
    assert out == expected


# ---- SSRF guard --------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://[::1]/",
        "file:///etc/passwd",
        "ftp://example.com/",
        "http:///no-host",
    ],
)
def test_assert_public_url_rejects_internal_and_bad_scheme(url: str) -> None:
    with pytest.raises(UrlFetchError):
        _assert_public_url(url)


def test_assert_public_url_allows_public_ip_literal() -> None:
    # Literal public IP — no DNS, no rejection.
    _assert_public_url("http://8.8.8.8/")


# ---- blob store containment -------------------------------------------


async def test_local_blob_store_rejects_traversal(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path)
    with pytest.raises(ValueError):
        await store.put("../escape.txt", b"x", "text/plain")


async def test_local_blob_store_round_trip(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path)
    key = await store.put("student-photos/abc-photo.png", b"data", "image/png")
    assert await store.get(key) == b"data"


# ---- production config guard ------------------------------------------


def _base_prod_kwargs(**over: object) -> dict[str, object]:
    kw: dict[str, object] = dict(
        environment="production",
        secret_key="x" * 40,
        email_provider="resend",
    )
    kw.update(over)
    return kw


def test_config_rejects_placeholder_secret_in_prod() -> None:
    with pytest.raises(ValueError):
        Settings(**_base_prod_kwargs(secret_key="change-me-in-production-this-is-a-dev-only-key"))  # type: ignore[arg-type]


def test_config_rejects_short_secret_in_prod() -> None:
    with pytest.raises(ValueError):
        Settings(**_base_prod_kwargs(secret_key="short-but-16-chars"))  # type: ignore[arg-type]


def test_config_rejects_mock_email_in_prod() -> None:
    with pytest.raises(ValueError):
        Settings(**_base_prod_kwargs(email_provider="mock"))  # type: ignore[arg-type]


def test_config_accepts_strong_prod_config() -> None:
    settings = Settings(**_base_prod_kwargs())  # type: ignore[arg-type]
    assert settings.environment == "production"


def test_config_allows_placeholder_in_dev() -> None:
    settings = Settings(  # type: ignore[call-arg]
        environment="development",
        secret_key="change-me-in-production-this-is-a-dev-only-key",
        email_provider="mock",
    )
    assert settings.environment == "development"


def test_config_rejects_wildcard_cors() -> None:
    with pytest.raises(ValueError):
        Settings(  # type: ignore[call-arg]
            environment="development",
            secret_key="change-me-in-production-this-is-a-dev-only-key",
            email_provider="mock",
            cors_origins="https://app.example.com,*",
        )


# ---- runtime middleware: security headers + CORS ------------------------


def test_responses_carry_security_headers() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert resp.headers["Content-Security-Policy"] == "frame-ancestors 'none'"
    # HSTS only makes sense on deployed (TLS) environments; tests aren't one.
    assert "Strict-Transport-Security" not in resp.headers


def test_cors_preflight_refuses_unknown_origin() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        resp = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
            },
        )
    assert "access-control-allow-origin" not in resp.headers


def test_cors_preflight_allows_configured_origin() -> None:
    from fastapi.testclient import TestClient

    from app.core.config import get_settings
    from app.main import app

    origin = get_settings().cors_origin_list[0]
    with TestClient(app) as client:
        resp = client.options(
            "/api/v1/auth/login",
            headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
        )
    assert resp.headers.get("access-control-allow-origin") == origin
    assert resp.headers.get("access-control-allow-credentials") == "true"
