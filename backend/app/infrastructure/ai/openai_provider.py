from __future__ import annotations

import json
from typing import Any

import httpx

from app.domain.providers.ai_provider import AIRawResponse
from app.infrastructure.ai.errors import (
    AIProviderParseError,
    AIProviderResponseError,
    AIProviderUnavailable,
)

OPENAI_DEFAULT_MODEL = "gpt-4o-mini"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider:
    name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = OPENAI_DEFAULT_MODEL,
        timeout_s: float = 60.0,
    ) -> None:
        if not api_key:
            raise AIProviderUnavailable("OPENAI_API_KEY is not set")
        self._api_key = api_key
        self.model = model
        self._timeout = timeout_s

    async def analyze_job(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> AIRawResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(OPENAI_URL, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise AIProviderUnavailable(f"OpenAI request failed: {exc}") from exc

        if resp.status_code >= 400:
            raise AIProviderResponseError(
                f"OpenAI returned {resp.status_code}: {resp.text[:500]}"
            )

        body = resp.json()
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderParseError(f"Unexpected OpenAI response shape: {body}") from exc

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIProviderParseError(
                f"OpenAI did not return JSON. First 500 chars: {content[:500]}"
            ) from exc

        if not isinstance(data, dict):
            raise AIProviderParseError("OpenAI response JSON was not an object")

        return AIRawResponse(data=data, provider=self.name, model=self.model)
