"""Unit tests for the shared uploaded-file store helper.

No DB/blob store — a tiny in-memory session + blob fake exercise the dedup
branch and the attacker-controlled-filename sanitisation.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from app.infrastructure.storage.uploaded_file_store import safe_filename, store_uploaded_file


class _FakeResult:
    def __init__(self, value: Any) -> None:
        self._value = value

    def scalar_one_or_none(self) -> Any:
        return self._value


class _FakeSession:
    """Minimal async-session stand-in: one preloaded dedup result."""

    def __init__(self, existing: Any = None) -> None:
        self.existing = existing
        self.added: list[Any] = []
        self.flushed = 0

    async def execute(self, _stmt: Any) -> _FakeResult:
        return _FakeResult(self.existing)

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        self.flushed += 1


class _FakeBlobs:
    name = "fake"

    def __init__(self) -> None:
        self.puts: dict[str, bytes] = {}

    async def put(self, key: str, content: bytes, _content_type: str) -> str:
        self.puts[key] = content
        return key

    async def get(self, key: str) -> bytes:
        if key in self.puts:
            return self.puts[key]
        raise FileNotFoundError(key)


def test_safe_filename_strips_paths_and_unsafe_chars() -> None:
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("my bug shot!.png") == "my_bug_shot_.png"
    assert safe_filename("") == "upload"
    assert safe_filename("///") == "upload"


async def test_store_uploaded_file_creates_row_and_writes_blob() -> None:
    session = _FakeSession(existing=None)
    blobs = _FakeBlobs()

    row = await store_uploaded_file(
        session,  # type: ignore[arg-type]
        blobs,  # type: ignore[arg-type]
        user_id=uuid4(),
        prefix="feedback-screenshots",
        filename="../evil path.png",
        content_type="image/png",
        content=b"abc",
    )

    assert row.content_type == "image/png"
    assert row.size_bytes == 3
    assert row in session.added
    assert session.flushed == 1
    # Blob written under a sanitised, prefixed, sha-based key.
    assert len(blobs.puts) == 1
    (key,) = blobs.puts
    assert key.startswith("feedback-screenshots/")
    assert ".." not in key
    assert key == row.storage_path


async def test_store_uploaded_file_dedups_existing() -> None:
    existing = SimpleNamespace(storage_path="stale/key")
    session = _FakeSession(existing=existing)
    blobs = _FakeBlobs()  # empty store → the dedup-hit blob "went missing"

    row = await store_uploaded_file(
        session,  # type: ignore[arg-type]
        blobs,  # type: ignore[arg-type]
        user_id=uuid4(),
        prefix="feedback-screenshots",
        filename="dup.png",
        content_type="image/png",
        content=b"same-bytes",
    )

    assert row is existing
    assert session.added == []
    assert len(blobs.puts) == 1
    assert row.storage_path != "stale/key"
    assert row.storage_path.startswith("feedback-screenshots/")
