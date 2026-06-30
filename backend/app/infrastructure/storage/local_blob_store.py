"""LocalBlobStore — filesystem-backed blob store for dev.

Writes under `base_dir` and returns paths relative to that root as keys.
Mirrors the pattern Phase D's ingestion services were already using; the
abstraction just lets prod swap GCS in without code changes.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalBlobStore:
    name = "local"

    def __init__(self, base_dir: Path) -> None:
        self._base = base_dir

    async def put(self, key: str, content: bytes, content_type: str) -> str:
        # The key is what we persist in the DB; the actual file is at
        # base_dir / key. Returning the key (not the full path) keeps
        # put/get symmetric and makes legacy-path migration optional.
        path = self._base / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key

    async def get(self, key: str) -> bytes:
        # Legacy rows (pre-blob-store) may hold an absolute path; honor
        # those without rejoining base_dir. New rows hold a relative key.
        path = Path(key)
        if not path.is_absolute():
            path = self._base / key
        if not path.exists():
            raise FileNotFoundError(key)
        return path.read_bytes()
