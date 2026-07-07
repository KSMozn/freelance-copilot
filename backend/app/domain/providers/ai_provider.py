from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class AIRawResponse:
    """A provider returns a parsed JSON object plus identification metadata.

    Validation against task-specific Pydantic schemas (analyzer, proposal, …)
    happens in the application layer so the domain stays decoupled.

    `usage` is populated when the underlying HTTP response includes a
    `usage` field (OpenAI-compatible providers do). Consumers log it into
    `usage_events.meta` so the admin panel can aggregate LLM spend.
    Shape: `{"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}`.
    """

    data: dict[str, Any]
    provider: str
    model: str
    usage: dict[str, int] | None = None


class AIProvider(Protocol):
    """Outbound port for any LLM that returns a structured JSON object.

    `complete_json` handles all text-only JSON tasks (analysis, proposal
    generation, future review passes). `complete_json_with_image` handles
    multimodal tasks where the user supplies an image alongside the prompt
    (e.g. importing a job from an Upwork screenshot).
    """

    name: str
    model: str

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> AIRawResponse: ...

    async def complete_json_with_image(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_bytes: bytes,
        image_mime_type: str,
    ) -> AIRawResponse: ...
