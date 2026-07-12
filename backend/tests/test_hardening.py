"""Tests for the security-hardening quick-wins."""
from __future__ import annotations

from pathlib import Path
from tempfile import SpooledTemporaryFile

import pytest
from fastapi import HTTPException, UploadFile

from app.api.uploads import read_upload_limited
from app.application.services.student_profile_service import _safe_filename
from app.core.config import Settings, get_settings
from app.core.rate_limit import SlidingWindowLimiter, otp_request_ip_limiter
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


def test_otp_request_ip_limit_is_configured_not_hardcoded() -> None:
    # The dev/e2e compose stack raises OTP_REQUEST_IP_LIMIT_PER_MIN (one
    # runner IP signs in every e2e account); production must keep 8.
    assert otp_request_ip_limiter.limit == get_settings().otp_request_ip_limit_per_min
    assert Settings.model_fields["otp_request_ip_limit_per_min"].default == 8


# ---- bounded uploads --------------------------------------------------


async def test_read_upload_limited_reads_only_one_byte_past_cap() -> None:
    upload = UploadFile(file=SpooledTemporaryFile(), filename="large.bin")
    await upload.write(b"123456")
    await upload.seek(0)

    with pytest.raises(HTTPException) as exc:
        await read_upload_limited(upload, max_bytes=4, detail="Too large")

    assert exc.value.status_code == 413
    assert exc.value.detail == "Too large"
    assert await upload.read() == b"6"


async def test_read_upload_limited_returns_content_within_cap() -> None:
    upload = UploadFile(file=SpooledTemporaryFile(), filename="small.bin")
    await upload.write(b"1234")
    await upload.seek(0)

    assert await read_upload_limited(upload, max_bytes=4, detail="Too large") == b"1234"


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
        "http://100.64.0.1/",  # CGNAT — only caught by the is_global predicate
        "http://[::1]/",
        "file:///etc/passwd",
        "ftp://example.com/",
        "http:///no-host",
    ],
)
async def test_assert_public_url_rejects_internal_and_bad_scheme(url: str) -> None:
    with pytest.raises(UrlFetchError):
        await _assert_public_url(url)


async def test_assert_public_url_allows_public_ip_literal() -> None:
    # Literal public IP — no DNS, no rejection.
    await _assert_public_url("http://8.8.8.8/")


# ---- SSRF guard: redirect hops (fetch_page manual-redirect loop) --------
#
# A public URL must not be able to 302-bounce the fetch into an internal
# address. DNS is faked (public hostname → public IP, internal names →
# private IPs) and the HTTP layer is a MockTransport, so no test traffic
# leaves the process.

_REDIRECTS = {
    "https://safe-public.example/to-metadata": "http://169.254.169.254/latest/meta-data/",
    "https://safe-public.example/to-localhost": "http://localhost/admin",
    "https://safe-public.example/to-private": "http://internal.corp/secrets",
    "https://safe-public.example/to-final": "https://safe-public.example/final",
}

_FAKE_DNS = {
    "safe-public.example": "93.184.216.34",  # public
    "internal.corp": "10.0.0.5",  # private
    "localhost": "127.0.0.1",  # loopback
}


def _install_fetch_fakes(monkeypatch: pytest.MonkeyPatch) -> None:
    import ipaddress
    import socket as socket_mod

    import httpx

    from app.infrastructure.http import url_fetcher

    def fake_getaddrinfo(host, port, *args, **kwargs):  # type: ignore[no-untyped-def]
        ip = _FAKE_DNS.get(host, host)
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise socket_mod.gaierror(f"fake DNS has no entry for {host!r}") from None
        return [(socket_mod.AF_INET, socket_mod.SOCK_STREAM, 6, "", (ip, port or 80))]

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url in _REDIRECTS:
            return httpx.Response(302, headers={"location": _REDIRECTS[url]})
        return httpx.Response(
            200, html="<html><title>Safe</title><body>public content</body></html>"
        )

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(url_fetcher.socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(
        url_fetcher.httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=transport, **kw),
    )


@pytest.mark.parametrize(
    "path",
    ["to-metadata", "to-localhost", "to-private"],
)
async def test_fetch_page_blocks_redirect_to_internal_address(
    monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    from app.infrastructure.http.url_fetcher import fetch_page

    _install_fetch_fakes(monkeypatch)
    with pytest.raises(UrlFetchError, match=r"non-public|Cannot resolve"):
        await fetch_page(f"https://safe-public.example/{path}")


async def test_fetch_page_follows_public_redirect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Positive control: a public→public redirect still works."""
    from app.infrastructure.http.url_fetcher import fetch_page

    _install_fetch_fakes(monkeypatch)
    page = await fetch_page("https://safe-public.example/to-final")
    assert page.final_url == "https://safe-public.example/final"
    assert page.title == "Safe"
    assert "public content" in page.text


async def test_fetch_page_stops_streaming_at_raw_size_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import httpx

    from app.infrastructure.http import url_fetcher

    real_client = httpx.AsyncClient
    _install_fetch_fakes(monkeypatch)
    monkeypatch.setattr(url_fetcher, "MAX_BYTES", 16)
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"x" * 17)
    )
    monkeypatch.setattr(
        url_fetcher.httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=transport, **kw),
    )

    with pytest.raises(UrlFetchError, match="Response too large"):
        await url_fetcher.fetch_page("https://safe-public.example/oversized")


async def test_fetch_page_preserves_declared_response_charset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import httpx

    from app.infrastructure.http import url_fetcher

    real_client = httpx.AsyncClient
    _install_fetch_fakes(monkeypatch)
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "text/html; charset=iso-8859-1"},
            content="<html><title>Café</title><body>Résumé</body></html>".encode(
                "iso-8859-1"
            ),
        )
    )
    monkeypatch.setattr(
        url_fetcher.httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=transport, **kw),
    )

    page = await url_fetcher.fetch_page("https://safe-public.example/latin-1")
    assert page.title == "Café"
    assert page.text == "Café Résumé"


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


def test_oversized_upload_is_rejected_before_auth_or_multipart_parsing() -> None:
    from fastapi.testclient import TestClient

    from app.core.config import get_settings
    from app.core.request_size_limit import MAX_REQUEST_BODY_BYTES
    from app.main import app

    origin = get_settings().cors_origin_list[0]
    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/students/profile/photo",
            content=b"x" * (MAX_REQUEST_BODY_BYTES + 1),
            headers={
                "content-type": "multipart/form-data; boundary=unused",
                "origin": origin,
            },
        )

    assert resp.status_code == 413
    assert resp.json() == {"detail": "Request body too large"}
    assert resp.headers["access-control-allow-origin"] == origin
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"


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
