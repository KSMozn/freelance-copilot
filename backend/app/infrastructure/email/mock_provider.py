from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.domain.providers.email_provider import (
    EmailMessage,
    EmailSendResult,
)

logger = logging.getLogger(__name__)

# Single shared path that the dev workflow checks for OTP codes.
DEFAULT_DEV_OUTBOX = Path("var/dev-emails.jsonl")

# Match the 6-digit code in the templated body so dev logs surface it
# without operators having to grep the JSONL.
_CODE_RE = re.compile(r"\b(\d{6})\b")


class MockEmailProvider:
    """Writes outgoing emails to a JSONL file and logs the OTP code.

    Used in dev/test so the OTP signup flow can be exercised end-to-end
    without an email service.
    """

    name = "mock"

    def __init__(self, outbox_path: Path | None = None) -> None:
        self._outbox = outbox_path or DEFAULT_DEV_OUTBOX

    async def send(self, message: EmailMessage) -> EmailSendResult:
        self._outbox.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now(UTC).isoformat(),
            "to": message.to,
            "subject": message.subject,
            "text_body": message.text_body,
            "tags": message.tags or {},
        }
        with self._outbox.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

        # Surface the code in stdout so developers don't have to tail the file
        # if they're already watching the logs.
        match = _CODE_RE.search(message.text_body)
        if match:
            logger.warning(
                "[mock-email] OTP for %s → %s (subject=%r)",
                message.to,
                match.group(1),
                message.subject,
            )
        else:
            logger.info("[mock-email] %s → %s", message.subject, message.to)

        return EmailSendResult(provider=self.name, message_id=str(uuid4()))
