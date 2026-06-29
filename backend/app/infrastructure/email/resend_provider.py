from __future__ import annotations

import httpx

from app.domain.providers.email_provider import (
    EmailMessage,
    EmailSendResult,
)
from app.infrastructure.email.errors import (
    EmailProviderError,
    EmailProviderUnavailable,
)

RESEND_API_URL = "https://api.resend.com/emails"


class ResendEmailProvider:
    """Sends email via Resend (https://resend.com).

    `from_address` must be on a sender domain verified in the Resend dashboard.
    The free tier covers up to 3K messages per month, which fits the early
    user trajectory; switch to SES or similar at scale.
    """

    name = "resend"

    def __init__(
        self,
        *,
        api_key: str,
        from_address: str,
        from_name: str | None = None,
        timeout_s: float = 15.0,
    ) -> None:
        if not api_key:
            raise EmailProviderUnavailable("RESEND_API_KEY is not set")
        if not from_address:
            raise EmailProviderUnavailable("RESEND_FROM_EMAIL is not set")
        self._api_key = api_key
        self._from = (
            f"{from_name} <{from_address}>" if from_name else from_address
        )
        self._timeout = timeout_s

    async def send(self, message: EmailMessage) -> EmailSendResult:
        payload = {
            "from": self._from,
            "to": [message.to],
            "subject": message.subject,
            "html": message.html_body,
            "text": message.text_body,
        }
        if message.tags:
            payload["tags"] = [
                {"name": k, "value": v} for k, v in message.tags.items()
            ]

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(RESEND_API_URL, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise EmailProviderError(f"Resend request failed: {exc}") from exc

        if resp.status_code >= 400:
            raise EmailProviderError(
                f"Resend returned {resp.status_code}: {resp.text[:500]}"
            )

        body = resp.json()
        return EmailSendResult(provider=self.name, message_id=body.get("id"))
