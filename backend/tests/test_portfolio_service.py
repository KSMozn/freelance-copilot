from uuid import uuid4

import pytest

from app.application.dto.portfolio_dto import PortfolioCreate, PortfolioUpdate
from app.application.services.portfolio_service import (
    PORTFOLIO_OWNER_TYPE,
    PortfolioService,
)
from app.domain.exceptions import NotFoundError
from app.infrastructure.ai.mock_embedding_provider import MockEmbeddingProvider
from tests.factories import (
    FakeEmbeddingRepository,
    FakePortfolioRepository,
)


def _service() -> tuple[PortfolioService, FakePortfolioRepository, FakeEmbeddingRepository, MockEmbeddingProvider]:
    portfolios = FakePortfolioRepository()
    embeddings = FakeEmbeddingRepository()
    provider = MockEmbeddingProvider()
    svc = PortfolioService(
        portfolio_repo=portfolios,
        embedding_repo=embeddings,
        embedding_provider=provider,
    )
    return svc, portfolios, embeddings, provider


def _create_payload(**overrides):  # type: ignore[no-untyped-def]
    base = dict(
        title="Customer 360 Analytics Platform",
        short_description="Customer 360 on PostgreSQL",
        long_description="Designed and shipped a customer-360 platform on PostgreSQL.",
        role="Lead Engineer",
        business_domain="Enterprise SaaS",
        technologies=["PostgreSQL", "Python", "FastAPI"],
        skills=["PostgreSQL", "Data modeling", "Analytics"],
        features=["Wide customer table"],
        outcomes=["Sub-second queries"],
        highlight=True,
    )
    base.update(overrides)
    return PortfolioCreate(**base)


async def test_create_persists_and_generates_embedding() -> None:
    svc, _, embeddings, provider = _service()
    user_id = uuid4()
    result = await svc.create(user_id, _create_payload())

    assert result.title == "Customer 360 Analytics Platform"
    assert result.skills == ["PostgreSQL", "Data modeling", "Analytics"]
    stored = await embeddings.get(
        owner_type=PORTFOLIO_OWNER_TYPE, owner_id=result.id, model=provider.model_id
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
    created = await svc.create(user_id, _create_payload())
    before = await embeddings.get(
        owner_type=PORTFOLIO_OWNER_TYPE, owner_id=created.id, model=provider.model_id
    )

    updated = await svc.update(
        user_id,
        created.id,
        PortfolioUpdate(
            title="Customer 360 Analytics Platform — extended",
            technologies=["PostgreSQL", "Python", "FastAPI", "Airflow"],
        ),
    )
    after = await embeddings.get(
        owner_type=PORTFOLIO_OWNER_TYPE, owner_id=created.id, model=provider.model_id
    )

    assert updated.title.endswith("extended")
    assert "Airflow" in updated.technologies
    assert before is not None and after is not None
    assert before != after, "embedding should change after meaningful edit"


async def test_delete_removes_portfolio_and_embedding() -> None:
    svc, portfolios, embeddings, provider = _service()
    user_id = uuid4()
    created = await svc.create(user_id, _create_payload())
    assert (
        await embeddings.get(
            owner_type=PORTFOLIO_OWNER_TYPE,
            owner_id=created.id,
            model=provider.model_id,
        )
        is not None
    )

    await svc.delete(user_id, created.id)
    assert await portfolios.get_by_id(created.id, user_id=user_id) is None
    assert (
        await embeddings.get(
            owner_type=PORTFOLIO_OWNER_TYPE,
            owner_id=created.id,
            model=provider.model_id,
        )
        is None
    )


async def test_list_filters_by_search_and_domain() -> None:
    svc, *_ = _service()
    user_id = uuid4()
    await svc.create(user_id, _create_payload(title="Customer 360 Analytics Platform"))
    await svc.create(
        user_id,
        _create_payload(
            title="LinkedIn Data Portability POC",
            business_domain="Government",
            long_description="OAuth + LinkedIn API portability export.",
            technologies=["OAuth", "Python"],
            skills=["OAuth", "Compliance"],
        ),
    )

    by_search = await svc.list(user_id, search="LinkedIn", domain=None, limit=10, offset=0)
    assert by_search.total == 1
    assert by_search.items[0].title.startswith("LinkedIn")

    by_domain = await svc.list(user_id, search=None, domain="Government", limit=10, offset=0)
    assert by_domain.total == 1
    assert by_domain.items[0].business_domain == "Government"


async def test_isolation_across_users() -> None:
    svc, *_ = _service()
    a = uuid4()
    b = uuid4()
    await svc.create(a, _create_payload(title="A's portfolio"))
    res = await svc.list(b, search=None, domain=None, limit=10, offset=0)
    assert res.total == 0
