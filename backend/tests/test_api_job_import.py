"""API-level test for the screenshot import endpoint."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.services.job_import_service import JobImportService
from app.application.services.job_service import JobService
from app.core.deps import get_current_user, get_job_import_service
from app.domain.entities.user import User
from app.infrastructure.ai.mock_provider import MockAIProvider
from app.main import app
from tests.factories import FakeJobRepository


_TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def user() -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        email="api-test@example.com",
        password_hash="x",
        full_name="Tester",
        is_active=True,
        is_superuser=False,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def client(user: User):  # type: ignore[no-untyped-def]
    repo = FakeJobRepository()

    async def _create(**kw):  # type: ignore[no-untyped-def]
        from datetime import UTC, datetime as dt
        from app.domain.entities.job import Job
        now = dt.now(UTC)
        job = Job(
            id=uuid4(),
            user_id=kw["user_id"],
            title=kw["title"],
            description=kw["description"],
            source_url=kw.get("source_url"),
            budget_type=kw.get("budget_type"),
            budget_min=kw.get("budget_min"),
            budget_max=kw.get("budget_max"),
            currency=kw.get("currency", "USD"),
            proposal_count=kw.get("proposal_count"),
            client_id=None,
            status=kw["status"],
            source_hash=kw["source_hash"],
            version=1,
            imported_at=now,
            created_at=now,
            updated_at=now,
        )
        repo._jobs[job.id] = job  # type: ignore[attr-defined]
        return job

    repo.create = _create  # type: ignore[assignment]
    job_service = JobService(repo)  # type: ignore[arg-type]

    def _import_service() -> JobImportService:
        return JobImportService(
            ai_provider=MockAIProvider(),
            job_service=job_service,
        )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_job_import_service] = _import_service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_import_image_requires_auth() -> None:
    with TestClient(app) as raw:
        resp = raw.post(
            "/api/v1/jobs/import-image",
            files={"image": ("x.png", _TINY_PNG, "image/png")},
        )
        assert resp.status_code == 401


def test_import_image_happy_path(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/jobs/import-image",
        files={"image": ("upwork.png", _TINY_PNG, "image/png")},
        data={"source_url": "https://www.upwork.com/jobs/~01abc"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "job" in body
    assert body["job"]["title"]
    assert body["job"]["source_url"] == "https://www.upwork.com/jobs/~01abc"
    assert "preview" in body
    assert isinstance(body["preview"]["mandatory_skills"], list)
    assert body["provider"] == "mock"


def test_import_image_rejects_pdf(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/jobs/import-image",
        files={"image": ("doc.pdf", b"%PDF-1.4 ...", "application/pdf")},
    )
    assert resp.status_code == 400


def test_import_image_rejects_empty_upload(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/jobs/import-image",
        files={"image": ("empty.png", b"", "image/png")},
    )
    assert resp.status_code == 400


def test_import_image_accepts_jpeg(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/jobs/import-image",
        files={"image": ("upwork.jpg", _TINY_PNG, "image/jpeg")},
    )
    assert resp.status_code == 201
