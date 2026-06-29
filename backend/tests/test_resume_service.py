from uuid import uuid4

import pytest

from app.application.dto.resume_dto import ResumeCreate, ResumeUpdate
from app.application.services.resume_service import RESUME_OWNER_TYPE, ResumeService
from app.domain.exceptions import NotFoundError
from app.infrastructure.ai.mock_embedding_provider import MockEmbeddingProvider
from tests.factories import FakeEmbeddingRepository, FakeResumeRepository


def _service() -> tuple[ResumeService, FakeResumeRepository, FakeEmbeddingRepository, MockEmbeddingProvider]:
    resumes = FakeResumeRepository()
    embeddings = FakeEmbeddingRepository()
    provider = MockEmbeddingProvider()
    svc = ResumeService(
        resume_repo=resumes, embedding_repo=embeddings, embedding_provider=provider
    )
    return svc, resumes, embeddings, provider


def _payload(**overrides):  # type: ignore[no-untyped-def]
    base = dict(
        title="AI / LLM Platform Resume",
        target_role="AI / Backend Engineer",
        summary="RAG + FastAPI + PostgreSQL backend engineer.",
        seniority_level="senior",
        primary_skills=["Python", "FastAPI", "RAG", "OpenAI"],
        secondary_skills=["PostgreSQL", "Docker"],
        industries=["AI SaaS"],
        domains=["AI SaaS"],
        achievements=["Shipped a production RAG platform."],
        project_highlights=["On-prem RAG over enterprise docs."],
        keywords=["RAG", "LLM"],
        notes=None,
    )
    base.update(overrides)
    return ResumeCreate(**base)


async def test_create_persists_and_embeds() -> None:
    svc, _, embeddings, provider = _service()
    user_id = uuid4()
    result = await svc.create(user_id, _payload())

    assert result.title == "AI / LLM Platform Resume"
    assert "Python" in result.primary_skills
    stored = await embeddings.get(
        owner_type=RESUME_OWNER_TYPE, owner_id=result.id, model=provider.model_id
    )
    assert stored is not None
    assert len(stored) == provider.dim


async def test_get_unknown_raises_not_found() -> None:
    svc, *_ = _service()
    with pytest.raises(NotFoundError):
        await svc.get(uuid4(), uuid4())


async def test_update_re_embeds() -> None:
    svc, _, embeddings, provider = _service()
    user_id = uuid4()
    created = await svc.create(user_id, _payload())
    before = await embeddings.get(
        owner_type=RESUME_OWNER_TYPE, owner_id=created.id, model=provider.model_id
    )
    updated = await svc.update(
        user_id,
        created.id,
        ResumeUpdate(
            title="AI / LLM Platform Resume — v2",
            primary_skills=["Python", "FastAPI", "RAG", "OpenAI", "Claude"],
        ),
    )
    after = await embeddings.get(
        owner_type=RESUME_OWNER_TYPE, owner_id=created.id, model=provider.model_id
    )
    assert updated.title.endswith("v2")
    assert "Claude" in updated.primary_skills
    assert before is not None and after is not None
    assert before != after


async def test_delete_removes_resume_and_embedding() -> None:
    svc, resumes, embeddings, provider = _service()
    user_id = uuid4()
    created = await svc.create(user_id, _payload())
    assert (
        await embeddings.get(
            owner_type=RESUME_OWNER_TYPE, owner_id=created.id, model=provider.model_id
        )
        is not None
    )

    await svc.delete(user_id, created.id)
    assert await resumes.get_by_id(created.id, user_id=user_id) is None
    assert (
        await embeddings.get(
            owner_type=RESUME_OWNER_TYPE, owner_id=created.id, model=provider.model_id
        )
        is None
    )


async def test_list_filters_by_search_domain_and_skill() -> None:
    svc, *_ = _service()
    user_id = uuid4()
    await svc.create(user_id, _payload(title="AI / LLM Platform Resume"))
    await svc.create(
        user_id,
        _payload(
            title="Engineering Manager Resume",
            target_role="Engineering Manager",
            summary="Player-coach EM for distributed teams.",
            primary_skills=["Engineering strategy", "Mentoring"],
            secondary_skills=["Hiring"],
            domains=["Enterprise SaaS"],
        ),
    )

    by_search = await svc.list(
        user_id, search="Manager", domain=None, skill=None, limit=10, offset=0
    )
    assert by_search.total == 1
    assert by_search.items[0].title.startswith("Engineering Manager")

    by_domain = await svc.list(
        user_id, search=None, domain="Enterprise SaaS", skill=None, limit=10, offset=0
    )
    assert by_domain.total == 1

    by_skill = await svc.list(
        user_id, search=None, domain=None, skill="RAG", limit=10, offset=0
    )
    assert by_skill.total == 1
    assert by_skill.items[0].title == "AI / LLM Platform Resume"


async def test_user_isolation() -> None:
    svc, *_ = _service()
    a = uuid4()
    b = uuid4()
    await svc.create(a, _payload(title="A's resume"))
    res = await svc.list(b, search=None, domain=None, skill=None, limit=10, offset=0)
    assert res.total == 0
