"""Deterministic feature-hashing embedding provider.

Same text always yields the same unit vector, and two texts with overlapping
tokens land closer than two unrelated texts. Good enough for tests, offline
demos, and as a fallback when no embedding key is configured.

We keep the output dim at 1536 so it slots into the existing pgvector column
shape without a separate schema branch for mock data.
"""
from __future__ import annotations

import hashlib
import math
import re

from app.domain.providers.embedding_provider import (
    EmbeddingProvider,  # noqa: F401 -- protocol assertion below
)

EMBEDDING_DIM = 1536
_TOKEN_RE = re.compile(r"[A-Za-z0-9_+#.\-]+")


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text) if len(t) > 1]


def _feature_hash(token: str) -> tuple[int, float]:
    h = hashlib.sha256(token.encode("utf-8")).digest()
    idx = int.from_bytes(h[:4], "big") % EMBEDDING_DIM
    sign = 1.0 if h[4] & 1 else -1.0
    return idx, sign


class MockEmbeddingProvider:
    name = "mock"
    model = "mock-hash-1536"
    dim = EMBEDDING_DIM

    @property
    def model_id(self) -> str:
        return f"{self.name}:{self.model}"

    async def embed(self, text: str) -> list[float]:
        vec = [0.0] * EMBEDDING_DIM
        for tok in _tokens(text):
            idx, sign = _feature_hash(tok)
            vec[idx] += sign
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0.0:
            # zero-vector cosine is undefined; return a tiny constant vector so
            # downstream code never divides by zero
            return [1.0 / math.sqrt(EMBEDDING_DIM)] * EMBEDDING_DIM
        return [x / norm for x in vec]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]
