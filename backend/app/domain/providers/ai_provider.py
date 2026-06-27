from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class AIRawResponse:
    """A provider returns a parsed JSON object plus identification metadata.

    Validation against the analyzer schema happens in the application layer so
    the domain stays decoupled from Pydantic.
    """

    data: dict[str, Any]
    provider: str
    model: str


class AIProvider(Protocol):
    """Outbound port for any LLM that can return a structured JSON object.

    Implementations live in `infrastructure/ai/`. Tests use a MockAIProvider so
    the application layer is exercised without network calls.
    """

    name: str
    model: str

    async def analyze_job(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> AIRawResponse: ...
