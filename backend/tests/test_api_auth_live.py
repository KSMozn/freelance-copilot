"""API tests for the live /auth surface (password + OTP flows).

A real AuthService is wired over `get_auth_service` with in-memory fakes
for the user repo, OTP repo, refresh-token store, and email provider —
no Postgres, no SMTP. Token minting, bcrypt hashing, and the OTP
issue/verify round-trip all run for real, so these tests exercise the
genuine wire contract the SPA depends on.
"""
from __future__ import annotations

import dataclasses
import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.services.auth_service import AuthService
from app.application.services.email_otp_service import EmailOtpService
from app.application.services.refresh_token_manager import RefreshTokenManager
from app.core.deps import get_auth_service
from app.core.security import create_refresh_token, decode_token
from app.domain.entities.email_otp import EmailOtp
from app.domain.entities.refresh_token import RefreshTokenRecord
from app.domain.entities.user import User
from app.domain.providers.email_provider import EmailMessage, EmailSendResult
from app.main import app


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


class FakeEmailOtpRepository:
    def __init__(self) -> None:
        self.rows: list[EmailOtp] = []

    async def create(
        self,
        *,
        email: str,
        code_hash: str,
        purpose: str,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
    ) -> EmailOtp:
        otp = EmailOtp(
            id=uuid4(),
            email=email,
            code_hash=code_hash,
            purpose=purpose,  # type: ignore[arg-type]
            expires_at=expires_at,
            consumed_at=None,
            attempts=0,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(UTC),
        )
        self.rows.append(otp)
        return otp

    async def delete(self, otp_id: UUID) -> None:
        self.rows = [otp for otp in self.rows if otp.id != otp_id]

    async def count_recent_issues(
        self, *, email: str, purpose: str, since: datetime
    ) -> int:
        return sum(
            1
            for o in self.rows
            if o.email == email and o.purpose == purpose and o.created_at >= since
        )

    async def get_active(self, *, email: str, purpose: str) -> EmailOtp | None:
        matching = [o for o in self.rows if o.email == email and o.purpose == purpose]
        return matching[-1] if matching else None

    async def increment_attempts(self, otp_id: UUID) -> None:
        for o in self.rows:
            if o.id == otp_id:
                o.attempts += 1

    async def mark_consumed(self, otp_id: UUID, consumed_at: datetime) -> bool:
        for o in self.rows:
            if o.id == otp_id and o.consumed_at is None:
                o.consumed_at = consumed_at
                return True
        return False


class FakeRefreshTokenRepository:
    """Just enough of the SQLAlchemy repo for issue/rotate to work."""

    def __init__(self) -> None:
        self.rows: dict[UUID, RefreshTokenRecord] = {}
        self.reject_password_bound_issue = False

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
        if expected_password_hash is not None and self.reject_password_bound_issue:
            return False
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
    otps = FakeEmailOtpRepository()
    otp_service = EmailOtpService(
        otp_repo=otps,
        email_provider=emails,
        app_name="Careero",
        from_address="no-reply@careero.test",
    )
    refresh_repo = FakeRefreshTokenRepository()
    service = AuthService(
        users,
        otp_service,
        None,  # persona provisioning is optional and DB-backed — skip it
        RefreshTokenManager(refresh_repo),
    )
    return {
        "users": users,
        "emails": emails,
        "otps": otps,
        "refresh_repo": refresh_repo,
        "service": service,
    }


@pytest.fixture
def client(state):  # type: ignore[no-untyped-def]
    app.dependency_overrides[get_auth_service] = lambda: state["service"]
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _sent_code(emails: FakeEmailProvider) -> str:
    match = re.search(r"\b(\d{6})\b", emails.sent[-1].subject)
    assert match, f"no 6-digit code in subject: {emails.sent[-1].subject!r}"
    return match.group(1)


# ---- password register + login -----------------------------------------


def test_register_creates_user_and_returns_tokens(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.student@example.com",
            "password": "s3cure-enough",
            "full_name": "New Student",
            "persona_kind": "student",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["user"]["email"] == "new.student@example.com"
    assert body["user"]["selected_persona_kind"] == "student"

    # The user actually landed in the store.
    stored = state["users"].rows[UUID(body["user"]["id"])]
    assert stored.password_hash is not None

    # Both tokens decode and belong to the user identity space.
    access = decode_token(body["tokens"]["access_token"], "access")
    refresh = decode_token(body["tokens"]["refresh_token"], "refresh")
    assert access["sub"] == body["user"]["id"]
    assert access["pt"] == "user"
    assert refresh["pt"] == "user"


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    payload = {"email": "dupe@example.com", "password": "s3cure-enough"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Email already registered"


def test_login_ok_returns_tokens(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "login.ok@example.com", "password": "s3cure-enough"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "login.ok@example.com", "password": "s3cure-enough"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user"]["email"] == "login.ok@example.com"
    assert decode_token(body["tokens"]["access_token"], "access")["pt"] == "user"


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "login.bad@example.com", "password": "s3cure-enough"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "login.bad@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"


def test_login_cannot_issue_session_after_password_changes(
    client: TestClient, state
) -> None:  # type: ignore[no-untyped-def]
    client.post(
        "/api/v1/auth/register",
        json={"email": "login.race@example.com", "password": "old-password-1"},
    )
    state["refresh_repo"].reject_password_bound_issue = True

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "login.race@example.com", "password": "old-password-1"},
    )

    assert resp.status_code == 401
    assert "sign in again" in resp.json()["detail"]


# ---- OTP flow ------------------------------------------------------------


def test_request_code_sends_otp_email(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/api/v1/auth/request-code",
        json={"email": "otp.new@example.com", "purpose": "register"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["sent"] is True
    assert body["expires_in_minutes"] > 0

    assert len(state["emails"].sent) == 1
    assert state["emails"].sent[0].to == "otp.new@example.com"
    assert _sent_code(state["emails"]).isdigit()


def test_verify_code_auto_creates_user_and_returns_tokens(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    client.post(
        "/api/v1/auth/request-code",
        json={"email": "otp.create@example.com", "purpose": "register"},
    )
    code = _sent_code(state["emails"])
    resp = client.post(
        "/api/v1/auth/verify-code",
        json={
            "email": "otp.create@example.com",
            "code": code,
            "purpose": "register",
            "full_name": "Otp Student",
            "persona_kind": "student",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user"]["email"] == "otp.create@example.com"
    assert body["user"]["email_verified_at"] is not None

    stored = state["users"].rows[UUID(body["user"]["id"])]
    assert stored.password_hash is None  # OTP-only account
    assert stored.selected_persona_kind == "student"
    assert decode_token(body["tokens"]["access_token"], "access")["pt"] == "user"


def test_verify_code_wrong_code_returns_400(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    client.post(
        "/api/v1/auth/request-code",
        json={"email": "otp.wrong@example.com", "purpose": "login"},
    )
    real = _sent_code(state["emails"])
    wrong = "000000" if real != "000000" else "111111"
    resp = client.post(
        "/api/v1/auth/verify-code",
        json={"email": "otp.wrong@example.com", "code": wrong, "purpose": "login"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Incorrect code."


def test_verify_code_expired_code_returns_400(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    from datetime import timedelta

    client.post(
        "/api/v1/auth/request-code",
        json={"email": "otp.expired@example.com", "purpose": "login"},
    )
    code = _sent_code(state["emails"])
    for row in state["otps"].rows:
        row.expires_at = datetime.now(UTC) - timedelta(minutes=1)

    resp = client.post(
        "/api/v1/auth/verify-code",
        json={"email": "otp.expired@example.com", "code": code, "purpose": "login"},
    )
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


def test_verify_code_cannot_be_reused(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    client.post(
        "/api/v1/auth/request-code",
        json={"email": "otp.reuse@example.com", "purpose": "register"},
    )
    code = _sent_code(state["emails"])
    payload = {"email": "otp.reuse@example.com", "code": code, "purpose": "register"}
    assert client.post("/api/v1/auth/verify-code", json=payload).status_code == 200

    resp = client.post("/api/v1/auth/verify-code", json=payload)
    assert resp.status_code == 400  # consumed on first use


def test_new_otp_supersedes_previous_code(
    client: TestClient, state, monkeypatch: pytest.MonkeyPatch
) -> None:  # type: ignore[no-untyped-def]
    codes = iter([111111, 222222])
    monkeypatch.setattr("app.application.services.email_otp_service.secrets.randbelow", lambda _: next(codes))
    request = {"email": "otp.superseded@example.com", "purpose": "register"}

    assert client.post("/api/v1/auth/request-code", json=request).status_code == 200
    first_code = _sent_code(state["emails"])
    assert client.post("/api/v1/auth/request-code", json=request).status_code == 200
    second_code = _sent_code(state["emails"])

    first = client.post(
        "/api/v1/auth/verify-code",
        json={**request, "code": first_code},
    )
    assert first.status_code == 400
    assert client.post(
        "/api/v1/auth/verify-code",
        json={**request, "code": second_code},
    ).status_code == 200


def test_lost_otp_claim_does_not_authenticate(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    request = {"email": "otp.race@example.com", "purpose": "register"}
    assert client.post("/api/v1/auth/request-code", json=request).status_code == 200
    code = _sent_code(state["emails"])

    async def lose_claim(otp_id: UUID, consumed_at: datetime) -> bool:
        return False

    state["otps"].mark_consumed = lose_claim
    response = client.post(
        "/api/v1/auth/verify-code",
        json={**request, "code": code},
    )

    assert response.status_code == 400
    assert state["users"].rows == {}


def test_request_code_provider_failure_returns_503(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    async def boom(message):  # type: ignore[no-untyped-def]
        raise RuntimeError("provider down")

    state["emails"].send = boom
    resp = client.post(
        "/api/v1/auth/request-code",
        json={"email": "otp.outage@example.com", "purpose": "login"},
    )
    assert resp.status_code == 503
    assert "couldn't send the email" in resp.json()["detail"]
    assert state["otps"].rows == []


# ---- /auth/me ------------------------------------------------------------


def test_me_with_valid_token_returns_user(client: TestClient) -> None:
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": "me.test@example.com", "password": "s3cure-enough"},
    ).json()
    token = registered["tokens"]["access_token"]

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == registered["user"]["id"]
    assert body["email"] == "me.test@example.com"
    assert body["is_active"] is True


def test_me_without_token_returns_401() -> None:
    with TestClient(app) as raw:
        resp = raw.get("/api/v1/auth/me")
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Not authenticated"


def test_me_disabled_user_with_valid_token_returns_401(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    """A still-valid access token must not outlive a disable action."""
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": "disabled.window@example.com", "password": "s3cure-enough"},
    ).json()
    token = registered["tokens"]["access_token"]
    state["users"].rows[UUID(registered["user"]["id"])].is_active = False

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "User is inactive"


# ---- identity-space separation on the refresh endpoint --------------------


def test_refresh_rejects_admin_refresh_token(client: TestClient) -> None:
    """An admin refresh token must bounce off the USER refresh endpoint."""
    admin_refresh = create_refresh_token(uuid4(), "admin")
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": admin_refresh})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not a user refresh token"


# ---- email case-insensitivity (mirrors the CITEXT column semantics) --------


def test_login_with_different_casing_reaches_same_account(client: TestClient) -> None:
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": "Case.Login@Example.com", "password": "s3cure-enough"},
    ).json()

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "case.login@EXAMPLE.COM", "password": "s3cure-enough"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["id"] == registered["user"]["id"]


def test_register_mixed_case_duplicate_returns_409(client: TestClient) -> None:
    first = client.post(
        "/api/v1/auth/register",
        json={"email": "Case.Dupe@Example.com", "password": "s3cure-enough"},
    )
    assert first.status_code == 201

    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "case.DUPE@example.com", "password": "s3cure-enough"},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Email already registered"


def test_otp_login_with_different_casing_uses_same_account(client: TestClient, state) -> None:  # type: ignore[no-untyped-def]
    """An OTP sign-in with different casing must NOT create a second account."""
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": "case.otp@example.com", "password": "s3cure-enough"},
    ).json()

    client.post(
        "/api/v1/auth/request-code",
        json={"email": "Case.OTP@EXAMPLE.com", "purpose": "login"},
    )
    code = _sent_code(state["emails"])
    resp = client.post(
        "/api/v1/auth/verify-code",
        json={"email": "Case.OTP@EXAMPLE.com", "code": code, "purpose": "login"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["id"] == registered["user"]["id"]
    assert len(state["users"].rows) == 1  # no duplicate account


# ---- login timing equalization --------------------------------------------


def test_login_unknown_email_burns_bcrypt_check(client: TestClient, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """A miss on the account lookup must still cost one bcrypt verification,
    otherwise response timing reveals which emails are registered."""
    calls: list[int] = []
    monkeypatch.setattr(
        "app.application.services.auth_service.dummy_verify_password",
        lambda: calls.append(1),
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost.nobody@example.com", "password": "whatever-pass"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"
    assert calls == [1]
