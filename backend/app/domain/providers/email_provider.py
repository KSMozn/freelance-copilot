from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class EmailMessage:
    to: str
    subject: str
    html_body: str
    text_body: str
    tags: dict[str, str] | None = None


@dataclass(slots=True)
class EmailSendResult:
    provider: str
    message_id: str | None


class EmailProvider(Protocol):
    """Outbound port for sending transactional email.

    Mirrors the `AIProvider` pattern — domain code constructs an `EmailMessage`
    and depends on this protocol; concrete providers live in
    `app/infrastructure/email/`.
    """

    name: str

    async def send(self, message: EmailMessage) -> EmailSendResult: ...
