"""API tests for the live /students surface (wizard CRUD + email coach).

Profile + entries endpoints run against a fake StudentProfileService
injected over the router-local `_service` dependency (the real one talks
to the ORM directly); the email coach is pure rules so it only needs the
user gate. No Postgres, no network.
"""
from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1.endpoints import students as students_endpoints
from app.application.dto.student_dto import StudentEntryUpsert, StudentLinks, StudentProfileUpdate
from app.core.deps import get_current_user
from app.domain.entities.user import User
from app.main import app


@pytest.fixture
def user() -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        email="student-api@example.com",
        password_hash="x",
        full_name="Student Tester",
        is_active=True,
        is_superuser=False,
        created_at=now,
        updated_at=now,
        selected_persona_kind="student",
    )


def _blank_profile(user_id: UUID) -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        user_id=user_id,
        full_name=None,
        professional_email=None,
        phone=None,
        location=None,
        date_of_birth=None,
        college=None,
        department=None,
        degree=None,
        major=None,
        graduation_year=None,
        gpa=None,
        photo_file_id=None,
        photo_offset_x=50,
        photo_offset_y=50,
        photo_zoom=100,
        summary=None,
        headline=None,
        links={},
        interests=[],
        completed_steps=[],
        current_step=None,
        cv_template_slug=None,
        created_at=now,
        updated_at=now,
    )


class FakeStudentProfileService:
    """In-memory stand-in exposing exactly what the endpoints call."""

    def __init__(self) -> None:
        self.profile: SimpleNamespace | None = None
        self.entries: dict[UUID, SimpleNamespace] = {}

    async def get_profile(self, user_id: UUID) -> SimpleNamespace | None:
        return self.profile

    async def upsert_profile(
        self, user_id: UUID, payload: StudentProfileUpdate
    ) -> SimpleNamespace:
        if self.profile is None:
            self.profile = _blank_profile(user_id)
        data = payload.model_dump(exclude_unset=True)
        mark_steps = data.pop("mark_steps", None)
        for key, value in data.items():
            if key == "links" and value is not None:
                links = dict(self.profile.links)
                for link_key, link_value in value.items():
                    if link_value is None:
                        links.pop(link_key, None)
                    else:
                        links[link_key] = link_value
                self.profile.links = links
            else:
                setattr(self.profile, key, value)
        for step in mark_steps or []:
            if step not in self.profile.completed_steps:
                self.profile.completed_steps.append(step)
        self.profile.updated_at = datetime.now(UTC)
        return self.profile

    async def list_entries(self, user_id: UUID) -> list[SimpleNamespace]:
        return list(self.entries.values())

    async def create_entry(
        self, user_id: UUID, payload: StudentEntryUpsert
    ) -> SimpleNamespace:
        now = datetime.now(UTC)
        row = SimpleNamespace(
            id=uuid4(), **payload.model_dump(), created_at=now, updated_at=now
        )
        self.entries[row.id] = row
        return row

    async def update_entry(
        self, user_id: UUID, entry_id: UUID, payload: StudentEntryUpsert
    ) -> SimpleNamespace | None:
        row = self.entries.get(entry_id)
        if row is None:
            return None
        for key, value in payload.model_dump().items():
            setattr(row, key, value)
        row.updated_at = datetime.now(UTC)
        return row

    async def delete_entry(self, user_id: UUID, entry_id: UUID) -> bool:
        return self.entries.pop(entry_id, None) is not None


@pytest.fixture
def svc() -> FakeStudentProfileService:
    return FakeStudentProfileService()


@pytest.fixture
def client(user: User, svc: FakeStudentProfileService):  # type: ignore[no-untyped-def]
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[students_endpoints._service] = lambda: svc
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# ---- auth gating ----------------------------------------------------------


def test_get_profile_requires_auth() -> None:
    with TestClient(app) as raw:
        assert raw.get("/api/v1/students/profile").status_code == 401


def test_coach_email_requires_auth() -> None:
    # Regression guard: this used to be the only unauthenticated /students
    # route — it now requires CurrentUser like everything else.
    with TestClient(app) as raw:
        resp = raw.post(
            "/api/v1/students/coach/email", json={"email": "someone@example.com"}
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Not authenticated"


# ---- profile ----------------------------------------------------------------


def test_get_profile_before_first_save_returns_null(client: TestClient) -> None:
    resp = client.get("/api/v1/students/profile")
    assert resp.status_code == 200
    assert resp.json() is None


def test_put_profile_round_trip(client: TestClient, user: User) -> None:
    resp = client.put(
        "/api/v1/students/profile",
        json={
            "full_name": "Sara Ali",
            "college": "Cairo University",
            "graduation_year": 2027,
            "mark_steps": ["basics"],
            "current_step": "education",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user_id"] == str(user.id)
    assert body["full_name"] == "Sara Ali"
    assert body["college"] == "Cairo University"
    assert body["graduation_year"] == 2027
    assert body["completed_steps"] == ["basics"]
    assert body["current_step"] == "education"

    # The saved state comes back on the next GET (wizard resume).
    again = client.get("/api/v1/students/profile").json()
    assert again["full_name"] == "Sara Ali"
    assert again["completed_steps"] == ["basics"]


def test_put_profile_can_clear_one_saved_link(client: TestClient) -> None:
    saved = client.put(
        "/api/v1/students/profile",
        json={
            "links": {
                "github": "https://github.com/student",
                "linkedin": "https://www.linkedin.com/in/student",
            }
        },
    )
    assert saved.status_code == 200, saved.text

    cleared = client.put(
        "/api/v1/students/profile",
        json={"links": {"github": None}},
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["links"] == {
        "linkedin": "https://www.linkedin.com/in/student"
    }


# ---- entries ----------------------------------------------------------------


def test_create_entry_and_list(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/students/entries",
        json={
            "kind": "project",
            "title": "Chess engine",
            "description": "A UCI chess engine in Python.",
            "details": {"tech_stack": ["Python"]},
        },
    )
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["kind"] == "project"
    assert created["title"] == "Chess engine"
    assert created["details"] == {"tech_stack": ["Python"]}

    listing = client.get("/api/v1/students/entries").json()
    assert [e["id"] for e in listing["items"]] == [created["id"]]


def test_update_entry(client: TestClient) -> None:
    created = client.post(
        "/api/v1/students/entries",
        json={"kind": "course", "title": "Databases I"},
    ).json()
    resp = client.put(
        f"/api/v1/students/entries/{created['id']}",
        json={"kind": "course", "title": "Databases II", "organization": "FCAI"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == created["id"]
    assert body["title"] == "Databases II"
    assert body["organization"] == "FCAI"


def test_update_missing_entry_returns_404(client: TestClient) -> None:
    resp = client.put(
        f"/api/v1/students/entries/{uuid4()}",
        json={"kind": "course", "title": "Ghost"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Entry not found"


def test_delete_entry(client: TestClient) -> None:
    created = client.post(
        "/api/v1/students/entries",
        json={"kind": "skill", "title": "SQL"},
    ).json()
    assert client.delete(f"/api/v1/students/entries/{created['id']}").status_code == 204
    assert client.get("/api/v1/students/entries").json()["items"] == []
    # Deleting again is a 404, not a silent success.
    assert client.delete(f"/api/v1/students/entries/{created['id']}").status_code == 404


# ---- email coach ------------------------------------------------------------


def test_coach_email_flags_suspicious_address(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/students/coach/email",
        json={"email": "xxx_cool_boy1999@gmail.com", "full_name": "Omar Hassan"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Coaching never blocks — warnings only.
    assert body["ok"] is True
    codes = {w["code"] for w in body["warnings"]}
    assert "email_unprofessional_word" in codes
    assert "email_too_many_digits" in codes
    # Name-based fallbacks are suggested on the same domain.
    values = [s["value"] for s in body["suggestions"]]
    assert "omar.hassan@gmail.com" in values


def test_coach_email_clean_address_passes(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/students/coach/email",
        json={"email": "omar.hassan@gmail.com", "full_name": "Omar Hassan"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"ok": True, "warnings": [], "suggestions": []}


def test_coach_email_malformed_address_blocks(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/students/coach/email", json={"email": "not-an-email"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
    assert body["warnings"][0]["code"] == "email_malformed"
    assert body["warnings"][0]["severity"] == "block"


# ---- validation -------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "url"),
    [
        ("github", "https://github.com.evil.example/student"),
        ("github", "https://evil.example/github.com/student"),
        ("linkedin", "https://linkedin.com.evil.example/in/student"),
        ("linkedin", "https://evil-linkedin.com/in/student"),
    ],
)
def test_profile_links_reject_deceptive_hosts(field: str, url: str) -> None:
    with pytest.raises(ValidationError):
        StudentLinks.model_validate({field: url})


def test_profile_links_allow_trusted_hosts_and_subdomains() -> None:
    links = StudentLinks(
        github="https://github.com/student",
        linkedin="https://www.linkedin.com/in/student",
    )
    assert links.github == "https://github.com/student"
    assert links.linkedin == "https://www.linkedin.com/in/student"


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example\\@github.com/student",
        "https://evil.example@github.com/student",
        "https://github.com%2fevil.example/student",
    ],
)
def test_trusted_profile_links_reject_parser_differentials(url: str) -> None:
    with pytest.raises(ValidationError):
        StudentLinks.model_validate({"github": url})


@pytest.mark.parametrize(
    "url",
    [
        "http://2130706433/path",
        "http://0x7f000001/path",
        "http://0177.0.0.1/path",
        "http://127.1/path",
        "http://2130706433./path",
        "http://0x7f000001./path",
    ],
)
def test_exported_links_reject_legacy_numeric_hosts(url: str) -> None:
    with pytest.raises(ValidationError):
        StudentLinks.model_validate({"website": url})


@pytest.mark.parametrize("scheme", ["javascript", "data", "file", "smb"])
def test_exported_links_reject_unsafe_schemes(scheme: str) -> None:
    with pytest.raises(ValidationError):
        StudentLinks.model_validate({"portfolio": f"{scheme}:payload"})
    with pytest.raises(ValidationError):
        StudentEntryUpsert.model_validate(
            {"kind": "project", "title": "Unsafe", "url": f"{scheme}:payload"}
        )


def test_survey_rating_out_of_bounds_returns_422(client: TestClient) -> None:
    resp = client.post("/api/v1/students/survey", json={"rating": 6})
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert isinstance(detail, list)  # Pydantic 422s return a detail array
    assert any("rating" in err["loc"] for err in detail)
