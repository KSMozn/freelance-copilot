"""UsageEventService — fire-and-forget log for the admin panel.

Every "meaningful" call in the app (coach LLM calls, CV renders, auth
events, admin actions) records a row here. The admin Activity view
paginates over them; the Overview aggregates over them.

`record()` returns a completed Task. Callers wrap it in `asyncio.create_task`
so the request thread isn't blocked on the log write. If the DB write
fails the event is dropped — logging must never break user requests.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import UUID, uuid4

# Strong references to in-flight background tasks so the event loop
# doesn't garbage-collect them mid-write (RUF006 / asyncio warning).
_BG_TASKS: set[asyncio.Task[Any]] = set()

from app.core.database import AsyncSessionLocal
from app.infrastructure.db.models.usage_event import UsageEvent

logger = logging.getLogger(__name__)


async def record(
    *,
    user_id: UUID | None,
    kind: str,
    status: str,
    duration_ms: int | None = None,
    error_message: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    """Append one usage_event row. Best-effort; swallows all errors.

    Uses its own AsyncSessionLocal — the caller's DB session is likely
    already committed / closed by the time we log.
    """
    try:
        async with AsyncSessionLocal() as session:
            row = UsageEvent(
                id=uuid4(),
                user_id=user_id,
                kind=kind,
                status=status,
                duration_ms=duration_ms,
                error_message=error_message[:2000] if error_message else None,
                meta=meta or {},
            )
            session.add(row)
            await session.commit()
    except Exception as exc:  # never let logging break a request
        logger.warning("Failed to record usage event %s: %s", kind, exc)


def fire(
    *,
    user_id: UUID | None,
    kind: str,
    status: str,
    duration_ms: int | None = None,
    error_message: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    """Schedule a background record() without awaiting it.

    Callers use this when they want zero latency impact — the log write
    lands after the response is returned. Loop-local; safe from any
    async context.
    """
    try:
        task = asyncio.create_task(
            record(
                user_id=user_id,
                kind=kind,
                status=status,
                duration_ms=duration_ms,
                error_message=error_message,
                meta=meta,
            )
        )
        _BG_TASKS.add(task)
        task.add_done_callback(_BG_TASKS.discard)
    except RuntimeError:
        # No running loop (e.g., during shutdown). Drop.
        pass
