"""The usage-event sink seam: background event writes are capturable in
tests and never touch a real database (see the autouse fixture in
conftest.py)."""
from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

from app.application.services import usage_event_service


async def test_fire_routes_through_the_sink(usage_events: list[dict[str, Any]]) -> None:
    user_id = uuid4()
    usage_event_service.fire(
        user_id=user_id,
        kind="test.kind",
        status="ok",
        duration_ms=12,
        meta={"a": 1},
    )
    # fire() schedules a background task — let it run.
    await asyncio.sleep(0)
    assert usage_events == [
        {
            "user_id": user_id,
            "kind": "test.kind",
            "status": "ok",
            "duration_ms": 12,
            "error_message": None,
            "meta": {"a": 1},
        }
    ]


async def test_sink_failures_are_swallowed() -> None:
    async def broken(_payload: dict[str, Any]) -> None:
        raise RuntimeError("sink exploded")

    usage_event_service.set_sink(broken)
    try:
        usage_event_service.fire(user_id=None, kind="test.kind", status="ok")
        await asyncio.sleep(0)  # must not raise anywhere
    finally:
        usage_event_service.set_sink(None)
