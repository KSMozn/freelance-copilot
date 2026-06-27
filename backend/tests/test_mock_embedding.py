import math

from app.infrastructure.ai.mock_embedding_provider import (
    EMBEDDING_DIM,
    MockEmbeddingProvider,
)


async def test_mock_embedding_is_deterministic() -> None:
    p = MockEmbeddingProvider()
    a = await p.embed("FastAPI PostgreSQL backend")
    b = await p.embed("FastAPI PostgreSQL backend")
    assert a == b
    assert len(a) == EMBEDDING_DIM


async def test_mock_embedding_is_unit_length() -> None:
    p = MockEmbeddingProvider()
    v = await p.embed("Some text to embed.")
    norm = math.sqrt(sum(x * x for x in v))
    assert abs(norm - 1.0) < 1e-9


async def test_similar_text_lands_closer_than_unrelated_text() -> None:
    p = MockEmbeddingProvider()
    base = await p.embed("Python FastAPI PostgreSQL backend for an AI SaaS")
    similar = await p.embed("Python FastAPI backend with PostgreSQL for AI SaaS company")
    unrelated = await p.embed("Vintage furniture restoration weekend hobby")

    def cos(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b, strict=True))

    sim_close = cos(base, similar)
    sim_far = cos(base, unrelated)
    assert sim_close > sim_far
    assert sim_close > 0.3  # generous floor — feature-hash sim is noisy on short text


async def test_empty_text_returns_well_defined_vector() -> None:
    p = MockEmbeddingProvider()
    v = await p.embed("")
    assert len(v) == EMBEDDING_DIM
    norm = math.sqrt(sum(x * x for x in v))
    assert abs(norm - 1.0) < 1e-6


async def test_model_id_disambiguates_providers() -> None:
    p = MockEmbeddingProvider()
    assert p.model_id.startswith("mock:")
    assert p.dim == EMBEDDING_DIM
