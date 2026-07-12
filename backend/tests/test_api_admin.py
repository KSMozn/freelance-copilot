"""API tests for the live /admin surface + the two-identity-space split.

The separation tests mint REAL JWTs via `app.core.security` and hit the
real gates: a `pt=user` token must bounce off /admin, and a `pt=admin`
token must bounce off /students — both fail on the `pt` claim before any
DB round-trip, so no Postgres is needed.

Endpoint bodies run against a fake AdminService injected over the
router-local `_service` dependency (the real one talks to the ORM
directly); the feedback-resolve route uses the session inline, so that
test fakes `get_session` instead.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints import admin as admin_endpoints
from app.application.dto.admin_dto import (
    AdminOverview,
    AdminUserDetail,
    AdminUserRow,
    LlmSpendSummary,
    WizardFunnel,
)
from app.core.deps import get_current_admin, get_session
from app.core.security import create_access_token, decode_token
from app.domain.entities.admin_user import AdminUser
from app.infrastructure.db.models.feedback_entry import FeedbackEntry
from app.main import app


@pytest.fixture
def admin() -> AdminUser:
    now = datetime.now(UTC)
    return AdminUser(
        id=uuid4(),
        email="root@personaarmory.test",
        password_hash="x",
        full_name="Root Admin",
        is_active=True,
        last_login_at=None,
        created_at=now,
        updated_at=now,
    )


def _make_user_row(**over: Any) -> AdminUserRow:
    defaults: dict[str, Any] = {
        "id": uuid4(),
        "email": "student@example.com",
        "full_name": "Student One",
        "persona_kind": "student",
        "is_active": True,
        "is_superuser": False,
        "email_verified": True,
        "last_login_at": None,
        "created_at": datetime.now(UTC),
        "wizard_step": "basics",
        "wizard_completed": 2,
        "has_linkedin": True,
        "has_github": False,
        "has_downloaded_cv": False,
    }
    defaults.update(over)
    return AdminUserRow(**defaults)


def _make_user_detail(user_id: UUID, email: str = "student@example.com") -> AdminUserDetail:
    return AdminUserDetail(
        id=user_id,
        email=email,
        full_name="Student One",
        persona_kind="student",
        is_active=True,
        is_superuser=False,
        email_verified_at=None,
        last_login_at=None,
        created_at=datetime.now(UTC),
        student=None,
    )


def _make_overview() -> AdminOverview:
    return AdminOverview(
        users_total=3,
        users_students=2,
        users_active_7d=1,
        signups_today=0,
        signups_7d=1,
        signups_30d=2,
        signups_series=[],
        funnel=WizardFunnel(
            registered=3,
            basics=2,
            education=2,
            photo=1,
            skills=1,
            courses=1,
            projects=1,
            internships=0,
            volunteer=0,
            languages=0,
            certificates=0,
            summary=0,
            preview=0,
            starter_pack=0,
            downloaded=0,
        ),
        entries_by_kind=[],
        usage_by_kind_7d=[],
        llm_spend_30d=LlmSpendSummary(
            total_calls=0,
            total_prompt_tokens=0,
            total_completion_tokens=0,
            total_cost_usd=0.0,
            by_model=[],
        ),
    )


class FakeAdminService:
    def __init__(
        self,
        rows: list[AdminUserRow] | None = None,
        details: dict[UUID, AdminUserDetail] | None = None,
    ) -> None:
        self.rows = rows or []
        self.details = details or {}

    async def list_users(self, **filters: Any) -> tuple[list[AdminUserRow], int]:
        return list(self.rows), len(self.rows)

    async def get_user_detail(self, user_id: UUID) -> AdminUserDetail | None:
        return self.details.get(user_id)

    async def get_overview(self) -> AdminOverview:
        return _make_overview()


def _client(admin: AdminUser, svc: FakeAdminService) -> TestClient:
    app.dependency_overrides[get_current_admin] = lambda: admin
    app.dependency_overrides[admin_endpoints._service] = lambda: svc
    return TestClient(app)


@pytest.fixture
def client(admin: AdminUser):  # type: ignore[no-untyped-def]
    target_id = uuid4()
    svc = FakeAdminService(
        rows=[_make_user_row()],
        details={target_id: _make_user_detail(target_id)},
    )
    try:
        yield _client(admin, svc), target_id
    finally:
        app.dependency_overrides.clear()


# ---- identity-space separation --------------------------------------------


def test_admin_overview_requires_token() -> None:
    with TestClient(app) as raw:
        resp = raw.get("/api/v1/admin/overview")
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Not authenticated"


def test_user_token_is_rejected_on_admin_routes() -> None:
    # A real, validly-signed USER access token must not open /admin — the
    # gate refuses on the pt claim before it ever loads an identity.
    user_token = create_access_token(uuid4(), "user")
    with TestClient(app) as raw:
        resp = raw.get(
            "/api/v1/admin/users", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Not an admin token"


def test_admin_token_is_rejected_on_student_routes() -> None:
    # Reverse direction: a real ADMIN access token must not open the user
    # surface (admin_users is a separate identity space from users).
    admin_token = create_access_token(uuid4(), "admin")
    headers = {"Authorization": f"Bearer {admin_token}"}
    with TestClient(app) as raw:
        for path in ("/api/v1/students/profile", "/api/v1/auth/me"):
            resp = raw.get(path, headers=headers)
            assert resp.status_code == 401, path
            assert resp.json()["detail"] == "Not a user token"


# ---- users ------------------------------------------------------------------


def test_list_users_returns_page_shape(client) -> None:  # type: ignore[no-untyped-def]
    c, _ = client
    resp = c.get("/api/v1/admin/users")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert body["page"] == 1
    assert body["size"] == 25
    row = body["items"][0]
    assert row["email"] == "student@example.com"
    assert row["persona_kind"] == "student"
    assert row["wizard_step"] == "basics"
    assert row["wizard_completed"] == 2


def test_overview_returns_aggregate_shape(client) -> None:  # type: ignore[no-untyped-def]
    c, _ = client
    resp = c.get("/api/v1/admin/overview")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["users_total"] == 3
    assert body["funnel"]["registered"] == 3
    assert body["llm_spend_30d"]["total_calls"] == 0
    assert body["usage_by_kind_7d"] == []


# ---- impersonation -----------------------------------------------------------


def test_impersonate_mints_short_lived_user_token(client, admin: AdminUser) -> None:  # type: ignore[no-untyped-def]
    c, target_id = client
    resp = c.post(f"/api/v1/admin/users/{target_id}/impersonate")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["target_user_id"] == str(target_id)
    assert body["target_user_email"] == "student@example.com"
    # Impersonation sessions are non-refreshable by contract.
    assert body["refresh_token"] == ""
    assert body["token_type"] == "bearer"

    claims = decode_token(body["access_token"], "access")
    assert claims["sub"] == str(target_id)
    assert claims["pt"] == "user"  # acts AS the user, not as the admin
    assert claims["imp"] is True
    assert claims["act"] == {"aid": str(admin.id), "email": admin.email}


def test_impersonate_unknown_user_returns_404(client) -> None:  # type: ignore[no-untyped-def]
    c, _ = client
    resp = c.post(f"/api/v1/admin/users/{uuid4()}/impersonate")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not found"


# ---- feedback resolve ---------------------------------------------------------


class _Result:
    def __init__(self, value: Any) -> None:
        self._value = value

    def scalar_one_or_none(self) -> Any:
        return self._value

    def one_or_none(self) -> Any:
        return self._value


class FakeSession:
    """Answers `execute()` from a scripted queue; records the commit."""

    def __init__(self, results: list[Any]) -> None:
        self._results = list(results)
        self.committed = False

    async def execute(self, _stmt: Any) -> _Result:
        return _Result(self._results.pop(0))

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, _row: Any) -> None:
        return None


def _feedback_row() -> FeedbackEntry:
    return FeedbackEntry(
        id=uuid4(),
        user_id=uuid4(),
        kind="general",
        rating=None,
        message="The wizard is great but the date pickers confused me.",
        template_slug=None,
        meta={},
        created_at=datetime.now(UTC),
        resolved_at=None,
    )


def test_resolve_feedback_marks_resolved(admin: AdminUser) -> None:
    row = _feedback_row()
    session = FakeSession(results=[row, ("student@example.com", "Student One")])

    async def _fake_session():  # type: ignore[no-untyped-def]
        yield session

    app.dependency_overrides[get_current_admin] = lambda: admin
    app.dependency_overrides[get_session] = _fake_session
    try:
        client = TestClient(app)
        resp = client.post(f"/api/v1/admin/feedback/{row.id}/resolve")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == str(row.id)
    assert body["resolved_at"] is not None
    assert body["resolved_by_email"] == admin.email
    assert body["user_email"] == "student@example.com"
    # The row itself was stamped and the change committed.
    assert session.committed is True
    assert row.meta["resolved_by_admin_id"] == str(admin.id)
    assert row.meta["resolved_by_email"] == admin.email


def test_resolve_feedback_unknown_returns_404(admin: AdminUser) -> None:
    session = FakeSession(results=[None])

    async def _fake_session():  # type: ignore[no-untyped-def]
        yield session

    app.dependency_overrides[get_current_admin] = lambda: admin
    app.dependency_overrides[get_session] = _fake_session
    try:
        client = TestClient(app)
        resp = client.post(f"/api/v1/admin/feedback/{uuid4()}/resolve")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Feedback not found"
    assert session.committed is False


# ---- identity-space separation on the ADMIN refresh endpoint ---------------


def test_admin_refresh_rejects_user_refresh_token() -> None:
    """A user refresh token must bounce off the ADMIN refresh endpoint.

    The pt-claim check fires before any repo access, so the service can be
    wired with inert placeholders — no admin lookup ever happens.
    """
    from app.api.v1.endpoints import admin_auth as admin_auth_endpoints
    from app.application.services.admin_auth_service import AdminAuthService
    from app.core.security import create_refresh_token

    service = AdminAuthService(None, object())  # type: ignore[arg-type]
    app.dependency_overrides[admin_auth_endpoints._service] = lambda: service
    try:
        client = TestClient(app)
        user_refresh = create_refresh_token(uuid4(), "user")
        resp = client.post(
            "/api/v1/admin/auth/refresh", json={"refresh_token": user_refresh}
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not an admin refresh token"


async def test_admin_login_unknown_email_burns_bcrypt_check(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Admin login must cost one bcrypt check even when the email is unknown,
    so response timing can't enumerate admin accounts."""
    from app.application.dto.admin_auth_dto import AdminLoginRequest
    from app.application.services.admin_auth_service import AdminAuthService
    from app.domain.exceptions import InvalidCredentialsError

    calls: list[int] = []
    monkeypatch.setattr(
        "app.application.services.admin_auth_service.dummy_verify_password",
        lambda: calls.append(1),
    )

    class MissRepo:
        async def get_by_email(self, email: str) -> None:
            return None

    service = AdminAuthService(MissRepo(), None)  # type: ignore[arg-type]
    with pytest.raises(InvalidCredentialsError):
        await service.login(
            AdminLoginRequest(email="ghost.admin@example.com", password="pw")
        )
    assert calls == [1]


# ---- X-Task-Secret machine endpoint ----------------------------------------


class _FakeDailyReportService:
    """Stands in for DailyReportService — the auth gate is what's under test."""

    def __init__(self, session: Any, email_provider: Any) -> None:
        pass

    async def build_report(self, *, window_hours: int) -> dict[str, Any]:
        return {}

    async def send(self, report: dict[str, Any]) -> Any:
        from app.application.dto.admin_dto import DailyReportResult

        return DailyReportResult(recipients=1, delivered=1, errors=[])


def _task_settings(**over: Any) -> Any:
    from app.core.config import get_settings

    return get_settings().model_copy(update=over)


def test_daily_report_unset_secret_outside_dev_returns_503(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        admin_endpoints,
        "get_settings",
        lambda: _task_settings(report_task_secret="", environment="staging"),
    )
    with TestClient(app) as raw:
        resp = raw.post("/api/v1/admin/tasks/daily-report", json={})
    assert resp.status_code == 503
    assert resp.json()["detail"] == "Task secret not configured"


def test_daily_report_wrong_secret_returns_401(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        admin_endpoints,
        "get_settings",
        lambda: _task_settings(report_task_secret="right-secret", environment="staging"),
    )
    with TestClient(app) as raw:
        resp = raw.post(
            "/api/v1/admin/tasks/daily-report",
            json={},
            headers={"X-Task-Secret": "wrong-secret"},
        )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid task secret"


def test_daily_report_correct_secret_runs_report(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        admin_endpoints,
        "get_settings",
        lambda: _task_settings(report_task_secret="right-secret", environment="staging"),
    )
    monkeypatch.setattr(admin_endpoints, "DailyReportService", _FakeDailyReportService)

    async def _no_session():  # type: ignore[no-untyped-def]
        yield None

    app.dependency_overrides[get_session] = _no_session
    try:
        client = TestClient(app)
        resp = client.post(
            "/api/v1/admin/tasks/daily-report",
            json={},
            headers={"X-Task-Secret": "right-secret"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    assert resp.json() == {"recipients": 1, "delivered": 1, "errors": []}
