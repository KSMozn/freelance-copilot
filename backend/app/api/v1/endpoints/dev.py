"""Dev-only mailbox: read what the mock email provider captured.

Exists so localhost sign-in is self-service — the OTP/reset email lands in
``var/dev-emails.jsonl`` and this endpoint surfaces it without shelling into
the container. Fail-closed: 404 unless the environment is ``development`` AND
the mock provider is active (staging/production additionally refuse to boot
with the mock provider at all).
"""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.application.dto.dev_dto import DevEmailRead, DevMailboxResponse
from app.core.deps import DevOutboxReaderDep, SettingsDep

router = APIRouter(prefix="/dev", tags=["dev"])


@router.get("/emails", response_model=DevMailboxResponse)
async def list_dev_emails(
    settings: SettingsDep,
    read_outbox: DevOutboxReaderDep,
    to: str | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> DevMailboxResponse:
    if settings.environment != "development" or settings.email_provider != "mock":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return DevMailboxResponse(
        emails=[DevEmailRead.model_validate(r) for r in read_outbox(to, limit)]
    )
