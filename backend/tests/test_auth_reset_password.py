"""API tests for the forgot/reset-password flow.

A real PasswordResetService (and AuthService, for the login/refresh
round-trips) is wired over the DI seams with in-memory fakes — no Postgres,
no email network. Token hashing, bcrypt password hashing, and refresh-token
revocation all run for real.

Rate-limiter state is reset per test by the conftest autouse fixture; tests
that only need a reset token in hand still mint it through the service
directly — it's faster and keeps each test focused on its own endpoint hits.
"""
from __future__ import annotations

import asyncio
import dataclasses
import re
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.services.auth_service import AuthService
from app.application.services.password_reset_service import PasswordResetService
from app.application.services.refresh_token_manager import RefreshTokenManager
from app.core.deps import get_auth_service, get_password_reset_service
from app.core.security import hash_password, verify_password
from app.domain.entities.password_reset_token import PasswordResetToken
from app.domain.entities.refresh_token import RefreshTokenRecord
from app.domain.entities.user import User
from app.domain.exceptions import EmailDeliveryError, PasswordResetInvalidError
from app.domain.providers.email_provider import EmailMessage, EmailSendResult


class FakeUserRepository:
    def __init__(self) -> None:
        self.rows: dict[UUID, User] = {}

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.rows.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        needle = str(email).strip().lower()
        return next((u for u in self.rows.values() if u.email == needle), None)

    async def create(
        self,
        *,
        email: str,
        password_hash: str | None,
        full_name: str | None,
        email_verified_at: datetime | None = None,
        selected_persona_kind: str = "professional",
    ) -> User:
        now = datetime.now(UTC)
        user = User(
            id=uuid4(),
            email=email.strip().lower(),
            password_hash=password_hash,
            full_name=full_name,
            is_active=True,
            is_superuser=False,
            created_at=now,
            updated_at=now,
            email_verified_at=email_verified_at,
            selected_persona_kind=selected_persona_kind,
        )
        self.rows[user.id] = user
        return user

    async def mark_email_verified(self, user_id: UUID, verified_at: datetime) -> None:
        user = self.rows.get(user_id)
        if user is not None:
            user.email_verified_at = verified_at

    async def touch_last_login(self, user_id: UUID, at: datetime) -> None:
        user = self.rows.get(user_id)
        if user is not None:
            user.last_login_at = at

    async def set_persona_kind(self, user_id: UUID, kind: str) -> None:
        user = self.rows.get(user_id)
        if user is not None:
            user.selected_persona_kind = kind

    async def set_password(self, user_id: UUID, password_hash: str) -> None:
        user = self.rows.get(user_id)
        if user is not None:
            user.password_hash = password_hash


class FakePasswordResetTokenRepository:
    def __init__(
        self,
        users: FakeUserRepository,
        refresh_tokens: FakeRefreshTokenRepository,
    ) -> None:
        self.rows: list[PasswordResetToken] = []
        self._users = users
        self._refresh_tokens = refresh_tokens

    async def create(
        self, *, user_id: UUID, token_hash: str, expires_at: datetime
    ) -> PasswordResetToken:
        # Strictly-increasing created_at, mirroring Postgres transaction
        # timestamps — invalidate_older_active_for_user orders rows by it.
        now = datetime.now(UTC)
        if self.rows and now <= self.rows[-1].created_at:
            now = self.rows[-1].created_at + timedelta(microseconds=1)
        token = PasswordResetToken(
            id=uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            used_at=None,
            created_at=now,
        )
        self.rows.append(token)
        return token

    async def get_by_token_hash(self, token_hash: str) -> PasswordResetToken | None:
        return next((t for t in self.rows if t.token_hash == token_hash), None)

    async def delete(self, token_id: UUID) -> None:
        self.rows = [token for token in self.rows if token.id != token_id]

    async def consume(
        self,
        *,
        token_id: UUID,
        user_id: UUID,
        password_hash: str,
        at: datetime,
    ) -> bool:
        for t in self.rows:
            if t.id == token_id and t.user_id == user_id and t.used_at is None:
                user = self._users.rows.get(user_id)
                if user is None or not user.is_active or t.expires_at < at:
                    return False
                t.used_at = at
                user.password_hash = password_hash
                if user.email_verified_at is None:
                    user.email_verified_at = at
                await self.invalidate_active_for_user(user_id, at)
                await self._refresh_tokens.revoke_all_for_subject(
                    "user", user_id, reason="password_reset", at=at
                )
                return True
        return False

    async def invalidate_active_for_user(self, user_id: UUID, at: datetime) -> None:
        for t in self.rows:
            if t.user_id == user_id and t.used_at is None:
                t.used_at = at

    async def invalidate_older_active_for_user(
        self, user_id: UUID, newest_token_id: UUID, at: datetime
    ) -> None:
        newest = next((t for t in self.rows if t.id == newest_token_id), None)
        if newest is None:
            return
        for token in self.rows:
            if (
                token.user_id == user_id
                and token.id != newest_token_id
                and token.used_at is None
                and token.created_at < newest.created_at
            ):
                token.used_at = at


class FakeRefreshTokenRepository:
    def __init__(self) -> None:
        self.rows: dict[UUID, RefreshTokenRecord] = {}

    async def create(
        self,
        *,
        jti,
        family_id,
        principal_type,
        subject_id,
        expires_at,
        expected_password_hash=None,
    ) -> bool:
        self.rows[jti] = RefreshTokenRecord(
            id=jti,
            family_id=family_id,
            principal_type=principal_type,
            subject_id=subject_id,
            expires_at=expires_at,
            revoked_at=None,
            revoked_reason=None,
            created_at=datetime.now(UTC),
        )
        return True

    async def get(self, jti: UUID) -> RefreshTokenRecord | None:
        return self.rows.get(jti)

    async def rotate(
        self,
        *,
        current_jti: UUID,
        new_jti: UUID,
        family_id: UUID,
        principal_type: str,
        subject_id: UUID,
        expires_at: datetime,
        at: datetime,
    ) -> bool:
        row = self.rows.get(current_jti)
        if (
            row is not None
            and row.revoked_at is None
            and row.expires_at > at
            and row.family_id == family_id
            and row.principal_type == principal_type
            and row.subject_id == subject_id
        ):
            self.rows[current_jti] = dataclasses.replace(
                row, revoked_at=at, revoked_reason="rotated"
            )
            self.rows[new_jti] = RefreshTokenRecord(
                id=new_jti,
                family_id=family_id,
                principal_type=principal_type,
                subject_id=subject_id,
                expires_at=expires_at,
                revoked_at=None,
                revoked_reason=None,
                created_at=at,
            )
            return True
        return False

    async def revoke_family(
        self,
        family_id: UUID,
        *,
        principal_type: str,
        subject_id: UUID,
        reason: str,
        at: datetime,
    ) -> None:
        for jti, row in list(self.rows.items()):
            if (
                row.family_id == family_id
                and row.principal_type == principal_type
                and row.subject_id == subject_id
                and row.revoked_at is None
            ):
                self.rows[jti] = dataclasses.replace(
                    row, revoked_at=at, revoked_reason=reason
                )

    async def revoke_all_for_subject(
        self, principal_type: str, subject_id: UUID, *, reason: str, at: datetime
    ) -> None:
        for jti, row in list(self.rows.items()):
            if (
                row.principal_type == principal_type
                and row.subject_id == subject_id
                and row.revoked_at is None
            ):
                self.rows[jti] = dataclasses.replace(
                    row, revoked_at=at, revoked_reason=reason
                )


class FakeEmailProvider:
    name = "fake"

    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    async def send(self, message: EmailMessage) -> EmailSendResult:
        self.sent.append(message)
        return EmailSendResult(provider=self.name, message_id="fake-id")


@pytest.fixture
def state():  # type: ignore[no-untyped-def]
    users = FakeUserRepository()
    emails = FakeEmailProvider()
    # Auth and reset share ONE refresh-token store so revocation on reset is
    # visible to /auth/refresh — same shape as production (same table).
    refresh_repo = FakeRefreshTokenRepository()
    resets = FakePasswordResetTokenRepository(users, refresh_repo)
    reset_service = PasswordResetService(
        user_repo=users,
        reset_repo=resets,
        reset_committer=resets,
        email_provider=emails,
        app_name="Careero",
        frontend_base_url="http://localhost:5173",
        expires_minutes=30,
    )
    auth_service = AuthService(
        users,
        None,  # OTP flow not under test here
        None,
        RefreshTokenManager(refresh_repo),
    )
    return {
        "users": users,
        "resets": resets,
        "emails": emails,
        "refresh_repo": refresh_repo,
        "reset_service": reset_service,
        "auth_service": auth_service,
    }


@pytest.fixture
def client(state):  # type: ignore[no-untyped-def]
    from app.main import app

    app.dependency_overrides[get_password_reset_service] = lambda: state["reset_service"]
    app.dependency_overrides[get_auth_service] = lambda: state["auth_service"]
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _sent_reset_token(emails: FakeEmailProvider) -> str:
    match = re.search(r"#token=([A-Za-z0-9_-]+)", emails.sent[-1].text_body)
    assert match, f"no reset token in body: {emails.sent[-1].text_body!r}"
    return match.group(1)


async def _mint_token(state, email: str) -> str:  # type: ignore[no-untyped-def]
    """Get a reset token via the service — doesn't burn endpoint rate limit."""
    await state["reset_service"].request_reset(email=email)
    return _sent_reset_token(state["emails"])


async def _create_user(state, email: str, password: str | None) -> User:  # type: ignore[no-untyped-def]
    """Seed a user through the fake repo — /auth/register shares a
    process-global per-IP limiter with the other test modules, so tests that
    only need an existing account must not spend that budget."""
    return await state["users"].create(
        email=email,
        password_hash=hash_password(password) if password else None,
        full_name=None,
    )


GENERIC_MESSAGE = "If this account exists, password reset instructions were sent."


# ---- POST /auth/forgot-password -------------------------------------------


async def test_forgot_password_sends_reset_email(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    await _create_user(state, "reset.happy@example.com", "old-password-1")
    resp = client.post(
        "/api/v1/auth/forgot-password", json={"email": "reset.happy@example.com"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"sent": True, "message": GENERIC_MESSAGE}

    sent = state["emails"].sent[-1]
    assert sent.to == "reset.happy@example.com"
    assert "reset" in sent.subject.lower()
    assert "http://localhost:5173/reset-password#token=" in sent.text_body
    # Stored hashed, never plaintext.
    token = _sent_reset_token(state["emails"])
    assert all(token != row.token_hash for row in state["resets"].rows)


async def test_failed_replacement_email_keeps_previous_reset_link(
    state,
) -> None:  # type: ignore[no-untyped-def]
    user = await _create_user(state, "reset.delivery@example.com", "old-password-1")
    previous_token = await _mint_token(state, user.email)
    previous_record = state["resets"].rows[-1]

    async def fail_delivery(message: EmailMessage) -> EmailSendResult:
        raise RuntimeError("provider down")

    state["emails"].send = fail_delivery
    with pytest.raises(EmailDeliveryError, match="couldn't send the email"):
        await state["reset_service"].request_reset(email=user.email)

    assert state["resets"].rows == [previous_record]
    assert previous_record.used_at is None
    await state["reset_service"].reset_password(
        token=previous_token,
        new_password="replacement-password-1",
    )
    assert verify_password(
        "replacement-password-1",
        state["users"].rows[user.id].password_hash,
    )


async def test_overlapping_reset_requests_leave_only_newest_link_active(
    state,
) -> None:  # type: ignore[no-untyped-def]
    """Issuance holds no lock across the provider call, so a second request
    runs to completion while the first send is still in flight — and the
    NEWEST-created link must win even though the first request finalizes
    last (its older-link burn is a no-op against the newer token)."""
    user = await _create_user(state, "reset.concurrent@example.com", "old-password-1")
    first_send_started = asyncio.Event()
    release_first_send = asyncio.Event()
    original_send = state["emails"].send
    send_count = 0

    async def controlled_send(message: EmailMessage) -> EmailSendResult:
        nonlocal send_count
        send_count += 1
        if send_count == 1:
            first_send_started.set()
            await release_first_send.wait()
        return await original_send(message)

    state["emails"].send = controlled_send
    first = asyncio.create_task(state["reset_service"].request_reset(email=user.email))
    await first_send_started.wait()
    # Runs to completion (create → send → finalize) while the first request
    # is parked inside its provider call — would deadlock under the old
    # serialized design.
    await state["reset_service"].request_reset(email=user.email)
    second_token = _sent_reset_token(state["emails"])

    release_first_send.set()
    await first
    first_token = _sent_reset_token(state["emails"])  # first's email sent last
    assert first_token != second_token

    with pytest.raises(PasswordResetInvalidError):
        await state["reset_service"].reset_password(
            token=first_token,
            new_password="first-overlap-password-1",
        )
    await state["reset_service"].reset_password(
        token=second_token,
        new_password="second-overlap-password-1",
    )


def test_forgot_password_unknown_email_returns_same_response(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/api/v1/auth/forgot-password", json={"email": "nobody.here@example.com"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"sent": True, "message": GENERIC_MESSAGE}
    assert state["emails"].sent == []  # nothing sent, nothing leaked


async def test_forgot_password_delivery_failure_returns_generic_response(
    client: TestClient, state
) -> None:  # type: ignore[no-untyped-def]
    await _create_user(state, "reset.outage@example.com", "old-password-1")

    async def fail_delivery(message: EmailMessage) -> EmailSendResult:
        raise RuntimeError("provider down")

    state["emails"].send = fail_delivery
    resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reset.outage@example.com"},
    )

    assert resp.status_code == 200
    assert resp.json() == {"sent": True, "message": GENERIC_MESSAGE}
    assert state["resets"].rows == []


def test_forgot_password_rate_limited_returns_429(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    email = "reset.limited@example.com"
    for _ in range(3):
        assert (
            client.post("/api/v1/auth/forgot-password", json={"email": email}).status_code
            == 200
        )
    resp = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert resp.status_code == 429


# ---- POST /auth/reset-password ---------------------------------------------


def test_reset_password_with_invalid_token_returns_400(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "not-a-real-token-at-all", "new_password": "new-password-1"},
    )
    assert resp.status_code == 400
    assert "invalid or has expired" in resp.json()["detail"]


async def test_reset_password_with_expired_token_returns_400(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    await state["users"].create(
        email="reset.expired@example.com",
        password_hash="irrelevant",
        full_name=None,
    )
    token = await _mint_token(state, "reset.expired@example.com")
    for row in state["resets"].rows:
        row.expires_at = datetime.now(UTC) - timedelta(minutes=1)

    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "new-password-1"},
    )
    assert resp.status_code == 400
    assert "invalid or has expired" in resp.json()["detail"]


async def test_reset_password_success_then_reuse_fails(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    await _create_user(state, "reset.success@example.com", "old-password-1")
    token = await _mint_token(state, "reset.success@example.com")

    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "brand-new-password-1"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"ok": True}

    # New password logs in; the old one doesn't.
    ok = client.post(
        "/api/v1/auth/login",
        json={"email": "reset.success@example.com", "password": "brand-new-password-1"},
    )
    assert ok.status_code == 200, ok.text
    old = client.post(
        "/api/v1/auth/login",
        json={"email": "reset.success@example.com", "password": "old-password-1"},
    )
    assert old.status_code == 401

    # Single-use: replaying the same link is rejected.
    again = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "another-password-1"},
    )
    assert again.status_code == 400


async def test_lost_reset_claim_does_not_change_password(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    user = await _create_user(state, "reset.race@example.com", "old-password-1")
    token = await _mint_token(state, user.email)

    async def lose_claim(**kwargs: object) -> bool:
        return False

    state["resets"].consume = lose_claim
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "brand-new-password-1"},
    )

    assert response.status_code == 400
    stored = state["users"].rows[user.id]
    assert stored.password_hash is not None
    assert verify_password("old-password-1", stored.password_hash)
    assert not verify_password("brand-new-password-1", stored.password_hash)


async def test_reset_password_revokes_existing_sessions(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    await _create_user(state, "reset.sessions@example.com", "old-password-1")
    logged_in = client.post(
        "/api/v1/auth/login",
        json={"email": "reset.sessions@example.com", "password": "old-password-1"},
    ).json()
    old_refresh = logged_in["tokens"]["refresh_token"]

    # Sanity: the refresh token works before the reset (and rotates).
    pre = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert pre.status_code == 200, pre.text
    rotated_refresh = pre.json()["refresh_token"]

    token = await _mint_token(state, "reset.sessions@example.com")
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "brand-new-password-1"},
    )
    assert resp.status_code == 200, resp.text

    # Every pre-reset session is dead — including the freshly rotated one.
    post = client.post("/api/v1/auth/refresh", json={"refresh_token": rotated_refresh})
    assert post.status_code == 401
    reasons = {r.revoked_reason for r in state["refresh_repo"].rows.values()}
    assert "password_reset" in reasons


async def test_reset_password_sets_first_password_for_otp_account(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    # OTP-created accounts are passwordless; a reset link (which proves inbox
    # control, same as OTP) is the supported way to add a password.
    user = await state["users"].create(
        email="reset.otp-only@example.com",
        password_hash=None,
        full_name="Otp Student",
    )
    token = await _mint_token(state, "reset.otp-only@example.com")
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "first-password-1"},
    )
    assert resp.status_code == 200, resp.text

    stored = state["users"].rows[user.id]
    assert stored.password_hash is not None
    assert verify_password("first-password-1", stored.password_hash)
    assert stored.email_verified_at is not None  # reset proves inbox control

    ok = client.post(
        "/api/v1/auth/login",
        json={"email": "reset.otp-only@example.com", "password": "first-password-1"},
    )
    assert ok.status_code == 200, ok.text


def test_reset_password_rejects_weak_password(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "whatever-token-value-x", "new_password": "short"},
    )
    assert resp.status_code == 422  # pydantic min_length=8, same as register


async def test_new_request_invalidates_previous_link(state) -> None:  # type: ignore[no-untyped-def]
    await state["users"].create(
        email="reset.rotate@example.com", password_hash=None, full_name=None
    )
    first = await _mint_token(state, "reset.rotate@example.com")
    second = await _mint_token(state, "reset.rotate@example.com")
    assert first != second

    from app.domain.exceptions import PasswordResetInvalidError

    with pytest.raises(PasswordResetInvalidError):
        await state["reset_service"].reset_password(
            token=first, new_password="new-password-1"
        )
    await state["reset_service"].reset_password(
        token=second, new_password="new-password-1"
    )
