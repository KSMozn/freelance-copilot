"""Service-level tests for the screenshot → job import flow."""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.dto.job_dto import JobListResponse
from app.application.services.job_import_service import (
    InvalidImageError,
    JobImportFailedError,
    JobImportService,
)
from app.application.services.job_service import JobService
from app.domain.providers.ai_provider import AIRawResponse
from app.infrastructure.ai.errors import AIProviderResponseError
from app.infrastructure.ai.mock_provider import MockAIProvider
from tests.factories import FakeJobRepository


# tiny well-formed PNG (1x1 transparent pixel) — just bytes, no actual content
_TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class _InMemoryJobService(JobService):
    """JobService backed by a FakeJobRepository — wraps the real service so
    JobImportService gets the same surface API the production path uses.
    """


def _make_service(provider=None) -> tuple[JobImportService, FakeJobRepository]:  # type: ignore[no-untyped-def]
    repo = FakeJobRepository()
    # Patch the in-memory repo with the small surface the JobService.create
    # path needs (creation, get_by_source_hash).
    async def create(**kw):  # type: ignore[no-untyped-def]
        from datetime import UTC, datetime
        from app.domain.entities.job import Job
        now = datetime.now(UTC)
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

    repo.create = create  # type: ignore[assignment]

    job_service = JobService(repo)  # type: ignore[arg-type]
    svc = JobImportService(
        ai_provider=provider or MockAIProvider(),
        job_service=job_service,
    )
    return svc, repo


async def test_rejects_empty_image() -> None:
    svc, _ = _make_service()
    with pytest.raises(InvalidImageError, match="Empty"):
        await svc.import_from_image(
            user_id=uuid4(),
            image_bytes=b"",
            image_mime_type="image/png",
        )


async def test_rejects_unsupported_mime() -> None:
    svc, _ = _make_service()
    with pytest.raises(InvalidImageError, match="Unsupported"):
        await svc.import_from_image(
            user_id=uuid4(),
            image_bytes=_TINY_PNG,
            image_mime_type="application/pdf",
        )


async def test_rejects_oversized_image() -> None:
    svc, _ = _make_service()
    huge = b"x" * (10 * 1024 * 1024 + 1)
    with pytest.raises(InvalidImageError, match="max is 10"):
        await svc.import_from_image(
            user_id=uuid4(),
            image_bytes=huge,
            image_mime_type="image/png",
        )


async def test_normalises_jpg_to_jpeg() -> None:
    svc, _ = _make_service()
    # image/jpg is not in the canonical allow-list, but the service normalises
    # it to image/jpeg before validating — must not raise.
    result = await svc.import_from_image(
        user_id=uuid4(),
        image_bytes=_TINY_PNG,
        image_mime_type="image/jpg",
    )
    assert result.job.title


async def test_mock_provider_creates_job_with_composed_description() -> None:
    svc, _ = _make_service()
    user_id = uuid4()
    result = await svc.import_from_image(
        user_id=user_id,
        image_bytes=_TINY_PNG,
        image_mime_type="image/png",
        source_url="https://www.upwork.com/jobs/~01abcdef",
    )

    job = result.job
    assert job.user_id == user_id
    assert job.title
    assert job.source_url == "https://www.upwork.com/jobs/~01abcdef"
    # Mock fills hourly 25-47 USD
    assert str(job.budget_type) == "hourly"
    assert job.budget_min == 25
    assert job.budget_max == 47

    # The description fold-in worked: skills + questions are in the body
    assert "Mandatory skills" in job.description
    assert "JavaScript" in job.description
    assert "Pre-application questions" in job.description

    # Preview surfaces the structured extras for the UI
    preview = result.preview
    assert "JavaScript" in preview.mandatory_skills
    assert ".NET Framework" in preview.nice_to_have_skills
    assert preview.experience_level == "Expert"
    assert preview.location == "Worldwide"
    assert len(preview.questions) >= 1


async def test_supplied_url_overrides_model_url() -> None:
    """User-supplied URL wins over whatever the model returned."""
    class _ProviderWithUrl:
        name = "fake"
        model = "fake"
        async def complete_json(self, *, system_prompt, user_prompt):  # noqa: D401
            raise NotImplementedError
        async def complete_json_with_image(self, **_kw):
            return AIRawResponse(
                data={
                    "title": "T",
                    "description": "D",
                    "source_url": "https://example.com/from-model",
                },
                provider=self.name,
                model=self.model,
            )

    svc, _ = _make_service(provider=_ProviderWithUrl())
    result = await svc.import_from_image(
        user_id=uuid4(),
        image_bytes=_TINY_PNG,
        image_mime_type="image/png",
        source_url="https://www.upwork.com/jobs/~01override",
    )
    assert result.job.source_url == "https://www.upwork.com/jobs/~01override"


async def test_empty_title_or_description_raises() -> None:
    class _BlankProvider:
        name = "fake"
        model = "fake"
        async def complete_json(self, *, system_prompt, user_prompt):
            raise NotImplementedError
        async def complete_json_with_image(self, **_kw):
            return AIRawResponse(
                data={"title": "", "description": ""},
                provider=self.name,
                model=self.model,
            )

    svc, _ = _make_service(provider=_BlankProvider())
    with pytest.raises(JobImportFailedError, match="Could not detect"):
        await svc.import_from_image(
            user_id=uuid4(), image_bytes=_TINY_PNG, image_mime_type="image/png"
        )


async def test_malformed_schema_raises() -> None:
    class _BadProvider:
        name = "fake"
        model = "fake"
        async def complete_json(self, *, system_prompt, user_prompt):
            raise NotImplementedError
        async def complete_json_with_image(self, **_kw):
            # Missing required `description`
            return AIRawResponse(
                data={"title": "Just a title"},
                provider=self.name,
                model=self.model,
            )

    svc, _ = _make_service(provider=_BadProvider())
    with pytest.raises(JobImportFailedError):
        await svc.import_from_image(
            user_id=uuid4(), image_bytes=_TINY_PNG, image_mime_type="image/png"
        )


async def test_provider_error_surfaces_as_import_failed() -> None:
    class _ExplodingProvider:
        name = "explode"
        model = "explode"
        async def complete_json(self, *, system_prompt, user_prompt):
            raise NotImplementedError
        async def complete_json_with_image(self, **_kw):
            raise AIProviderResponseError("upstream 503")

    svc, _ = _make_service(provider=_ExplodingProvider())
    with pytest.raises(JobImportFailedError, match="provider error"):
        await svc.import_from_image(
            user_id=uuid4(), image_bytes=_TINY_PNG, image_mime_type="image/png"
        )


# Smoke that JobListResponse stays a usable type (kept-around import)
def test_job_list_response_imports_ok() -> None:
    assert JobListResponse.__name__ == "JobListResponse"
