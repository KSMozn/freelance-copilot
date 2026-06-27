from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.domain.providers.ai_provider import AIRawResponse
from app.infrastructure.ai.errors import (
    AIProviderParseError,
    AIProviderResponseError,
    AIProviderUnavailable,
)

CLAUDE_DEFAULT_MODEL = "claude-sonnet-4-6"
CLAUDE_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_API_VERSION = "2023-06-01"


class ClaudeProvider:
    name = "claude"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = CLAUDE_DEFAULT_MODEL,
        timeout_s: float = 60.0,
        max_tokens: int = 2048,
    ) -> None:
        if not api_key:
            raise AIProviderUnavailable("ANTHROPIC_API_KEY is not set")
        self._api_key = api_key
        self.model = model
        self._timeout = timeout_s
        self._max_tokens = max_tokens

    async def analyze_job(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> AIRawResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self._max_tokens,
            "temperature": 0.2,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": CLAUDE_API_VERSION,
            "content-type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(CLAUDE_URL, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise AIProviderUnavailable(f"Anthropic request failed: {exc}") from exc

        if resp.status_code >= 400:
            raise AIProviderResponseError(
                f"Anthropic returned {resp.status_code}: {resp.text[:500]}"
            )

        body = resp.json()
        try:
            blocks = body["content"]
            text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        except (KeyError, TypeError) as exc:
            raise AIProviderParseError(f"Unexpected Anthropic response shape: {body}") from exc

        data = _extract_json_object(text)
        if data is None:
            raise AIProviderParseError(
                f"Anthropic did not return JSON. First 500 chars: {text[:500]}"
            )
        return AIRawResponse(data=data, provider=self.name, model=self.model)


def _extract_json_object(text: str) -> dict[str, Any] | None:
    """Find the first balanced JSON object in `text`.

    Claude is asked to return JSON only, but occasionally wraps it in prose or
    a fenced code block. We strip fences, then locate the outermost `{...}`.
    """
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    try:
        loaded = json.loads(cleaned)
        if isinstance(loaded, dict):
            return loaded
    except json.JSONDecodeError:
        pass

    depth = 0
    start = -1
    in_string = False
    escape = False
    for i, ch in enumerate(cleaned):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                snippet = cleaned[start : i + 1]
                try:
                    loaded = json.loads(snippet)
                    if isinstance(loaded, dict):
                        return loaded
                except json.JSONDecodeError:
                    return None
    return None
