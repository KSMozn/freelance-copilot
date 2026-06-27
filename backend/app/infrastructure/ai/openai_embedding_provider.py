from __future__ import annotations

import math
from typing import Any

import httpx

from app.infrastructure.ai.errors import (
    AIProviderParseError,
    AIProviderResponseError,
    AIProviderUnavailable,
)

OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
# text-embedding-3-small is 1536 dims; matches the pgvector column width.
_KNOWN_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


class OpenAIEmbeddingProvider:
    name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "text-embedding-3-small",
        timeout_s: float = 30.0,
    ) -> None:
        if not api_key:
            raise AIProviderUnavailable("OPENAI_API_KEY is not set")
        self._api_key = api_key
        self.model = model
        self.dim = _KNOWN_DIMS.get(model, 1536)
        self._timeout = timeout_s

    @property
    def model_id(self) -> str:
        return f"{self.name}:{self.model}"

    async def _request(self, texts: list[str]) -> list[list[float]]:
        payload: dict[str, Any] = {"model": self.model, "input": texts}
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(OPENAI_EMBEDDINGS_URL, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise AIProviderUnavailable(f"OpenAI embeddings request failed: {exc}") from exc

        if resp.status_code >= 400:
            raise AIProviderResponseError(
                f"OpenAI embeddings returned {resp.status_code}: {resp.text[:500]}"
            )

        body = resp.json()
        try:
            data = body["data"]
            vectors = [[float(x) for x in item["embedding"]] for item in data]
        except (KeyError, TypeError, ValueError) as exc:
            raise AIProviderParseError(
                f"Unexpected OpenAI embeddings response shape: {body}"
            ) from exc

        # Cosine math downstream assumes unit vectors. OpenAI returns
        # unnormalized embeddings — normalize here so providers are
        # interchangeable.
        return [_normalize(v) for v in vectors]

    async def embed(self, text: str) -> list[float]:
        return (await self._request([text]))[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await self._request(texts)
