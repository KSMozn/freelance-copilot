import os
from collections.abc import Iterator
from typing import Any

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key-please-change")
os.environ.setdefault("POSTGRES_USER", "upwork")
os.environ.setdefault("POSTGRES_PASSWORD", "upwork")
os.environ.setdefault("POSTGRES_DB", "upwork_intel_test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("ENVIRONMENT", "test")

from app.application.services import usage_event_service


@pytest.fixture(autouse=True)
def usage_events() -> Iterator[list[dict[str, Any]]]:
    """Route background usage-event writes into an in-memory list.

    Without this, endpoints that call `usage_event_service.fire(...)` spawn
    background tasks that attempt a REAL database connection (swallowed by
    design, but noisy at event-loop shutdown). Tests that want to assert on
    emitted events can simply take this fixture as an argument.
    """
    captured: list[dict[str, Any]] = []

    async def capture(payload: dict[str, Any]) -> None:
        captured.append(payload)

    usage_event_service.set_sink(capture)
    yield captured
    usage_event_service.set_sink(None)
