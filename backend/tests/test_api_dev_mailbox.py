"""Tests for the dev-only mailbox endpoint (GET /api/v1/dev/emails).

The endpoint must fail closed (404) outside development+mock, and read back
exactly what the MockEmailProvider captured when enabled.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.deps import get_dev_outbox_reader
from app.domain.providers.email_provider import EmailMessage
from app.infrastructure.email.mock_provider import MockEmailProvider, read_dev_outbox
from app.main import app


def _dev_settings():  # type: ignore[no-untyped-def]
    return get_settings().model_copy(
        update={"environment": "development", "email_provider": "mock"}
    )


@pytest.fixture
def outbox(tmp_path: Path) -> Path:
    return tmp_path / "dev-emails.jsonl"


@pytest.fixture
def client(outbox: Path):  # type: ignore[no-untyped-def]
    app.dependency_overrides[get_settings] = _dev_settings
    app.dependency_overrides[get_dev_outbox_reader] = lambda: (
        lambda to, limit: read_dev_outbox(to, limit, outbox_path=outbox)
    )
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


async def _send(outbox: Path, to: str, subject: str) -> None:
    provider = MockEmailProvider(outbox_path=outbox)
    await provider.send(
        EmailMessage(
            to=to,
            subject=subject,
            html_body="<p>body</p>",
            text_body="body",
            tags={"kind": "otp"},
        )
    )


def test_dev_emails_is_404_outside_development() -> None:
    # Tests run with ENVIRONMENT=test — the endpoint must not exist there,
    # and by extension not in staging/production either.
    with TestClient(app) as raw:
        resp = raw.get("/api/v1/dev/emails")
        assert resp.status_code == 404


@pytest.mark.parametrize(
    ("environment", "provider"),
    [
        ("production", "resend"),  # real prod config
        ("staging", "resend"),
        ("production", "mock"),  # can't boot for real (config validator), but
        ("staging", "mock"),  # the endpoint must still fail closed on its own
        ("development", "resend"),  # dev pointed at real email — no mailbox
    ],
)
def test_dev_emails_fails_closed_outside_dev_mock(environment: str, provider: str) -> None:
    """Production (or any non dev+mock) config must never expose captured mail.

    model_copy bypasses the boot validator on purpose: even if a misconfigured
    process somehow ran with these settings, the endpoint's own gate has to
    hold.
    """
    settings = get_settings().model_copy(
        update={
            "environment": environment,
            "email_provider": provider,
            "resend_api_key": "test-key",
        }
    )
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        with TestClient(app) as client:
            resp = client.get("/api/v1/dev/emails")
            assert resp.status_code == 404, (environment, provider, resp.text)
    finally:
        app.dependency_overrides.clear()


async def test_dev_emails_returns_captured_mail_newest_first(client: TestClient, outbox: Path) -> None:
    await _send(outbox, "one@example.com", "Your Careero sign-in code: 111111")
    await _send(outbox, "two@example.com", "Your Careero sign-in code: 222222")

    resp = client.get("/api/v1/dev/emails")
    assert resp.status_code == 200, resp.text
    emails = resp.json()["emails"]
    assert [e["to"] for e in emails] == ["two@example.com", "one@example.com"]
    assert emails[0]["subject"].endswith("222222")
    assert emails[0]["tags"] == {"kind": "otp"}


async def test_dev_emails_filters_by_recipient_case_insensitively(client: TestClient, outbox: Path) -> None:
    await _send(outbox, "target@example.com", "code: 333333")
    await _send(outbox, "other@example.com", "code: 444444")

    resp = client.get("/api/v1/dev/emails", params={"to": "Target@Example.com"})
    assert resp.status_code == 200, resp.text
    emails = resp.json()["emails"]
    assert len(emails) == 1
    assert emails[0]["to"] == "target@example.com"


def test_dev_emails_empty_outbox_returns_empty_list(client: TestClient) -> None:
    resp = client.get("/api/v1/dev/emails")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"emails": []}


# ---- mock provider captures the real auth emails ---------------------------


def _last_outbox_record(outbox: Path) -> dict[str, object]:
    import json

    record = json.loads(outbox.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert isinstance(record, dict)
    return record


async def test_otp_issue_is_captured_in_dev_outbox(outbox: Path) -> None:
    """The real EmailOtpService + MockEmailProvider round-trip: requesting a
    code must land it (readably) in the local outbox file."""
    from app.application.services.email_otp_service import EmailOtpService

    class _MinimalOtpRepo:
        async def create(self, **kwargs: object) -> None:
            return None

        async def count_recent_issues(self, **kwargs: object) -> int:
            return 0

    service = EmailOtpService(
        otp_repo=_MinimalOtpRepo(),  # type: ignore[arg-type]
        email_provider=MockEmailProvider(outbox_path=outbox),
        app_name="Careero",
        from_address="no-reply@careero.test",
    )
    await service.issue(email="captured.otp@example.com", purpose="login")

    import re

    record = _last_outbox_record(outbox)
    assert record["to"] == "captured.otp@example.com"
    assert record["tags"] == {"purpose": "login", "kind": "otp"}
    assert re.search(r"\b\d{6}\b", str(record["subject"]))


async def test_password_reset_email_is_captured_in_dev_outbox(outbox: Path) -> None:
    """Forgot-password through the real service + mock provider: the token
    link must be recoverable from the local outbox."""
    import re
    from datetime import UTC, datetime
    from uuid import uuid4

    from app.application.services.password_reset_service import PasswordResetService
    from app.domain.entities.user import User

    now = datetime.now(UTC)
    user = User(
        id=uuid4(),
        email="captured.reset@example.com",
        password_hash=None,
        full_name=None,
        is_active=True,
        is_superuser=False,
        created_at=now,
        updated_at=now,
    )

    class _MinimalUserRepo:
        async def get_by_email(self, email: str) -> User | None:
            return user if email == user.email else None

    class _MinimalResetRepo:
        async def create(self, **kwargs: object) -> None:
            return None

        async def invalidate_active_for_user(self, *args: object) -> None:
            return None

    service = PasswordResetService(
        user_repo=_MinimalUserRepo(),  # type: ignore[arg-type]
        reset_repo=_MinimalResetRepo(),  # type: ignore[arg-type]
        refresh_tokens=None,  # type: ignore[arg-type]  # not reached by request_reset
        email_provider=MockEmailProvider(outbox_path=outbox),
        app_name="Careero",
        frontend_base_url="http://localhost:5173",
    )
    await service.request_reset(email="captured.reset@example.com")

    record = _last_outbox_record(outbox)
    assert record["to"] == "captured.reset@example.com"
    assert record["tags"] == {"kind": "password_reset"}
    assert re.search(
        r"http://localhost:5173/reset-password\?token=[A-Za-z0-9_-]+",
        str(record["text_body"]),
    )
