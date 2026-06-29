"""LinkedInIngestService — parse a LinkedIn 'Save to PDF' export.

Same shape as CvIngestService but writes to ``linkedin_snapshots`` and
``uploaded_files`` instead of ``cv_uploads``. The structuring prompt is
identical for Phase D (LinkedIn PDFs look very CV-like); a
LinkedIn-specialized prompt is a Phase D.1 nice-to-have.
"""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from uuid import UUID

from app.application.services.cv_structuring import (
    structure_cv,
    to_dict,
)
from app.application.services.knowledge_graph_service import KnowledgeGraphService
from app.application.services.text_extraction import (
    TextExtractionError,
    extract_text,
)
from app.domain.entities.ingestion import LinkedInSnapshotEntry
from app.domain.providers.ai_provider import AIProvider
from app.domain.repositories.ingestion_repositories import (
    LinkedInSnapshotRepository,
    UploadedFileRepository,
)

logger = logging.getLogger(__name__)

UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", "var/uploads"))


class LinkedInIngestService:
    def __init__(
        self,
        *,
        snapshots: LinkedInSnapshotRepository,
        files: UploadedFileRepository,
        ai_provider: AIProvider,
        knowledge_graph: KnowledgeGraphService,
        uploads_dir: Path = UPLOADS_DIR,
    ) -> None:
        self._snapshots = snapshots
        self._files = files
        self._ai = ai_provider
        self._kg = knowledge_graph
        self._uploads_dir = uploads_dir

    async def ingest(
        self,
        *,
        user_id: UUID,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> LinkedInSnapshotEntry:
        sha = hashlib.sha256(content).hexdigest()
        size = len(content)

        # Reuse a registered blob row when present (cross-feature dedup —
        # the same file might back a certificate too).
        file_row = await self._files.get_by_sha(user_id=user_id, sha256=sha)
        if file_row is None:
            self._uploads_dir.mkdir(parents=True, exist_ok=True)
            path = self._uploads_dir / sha
            if not path.exists():
                try:
                    path.write_bytes(content)
                except OSError as exc:
                    logger.warning("Failed to write LinkedIn blob: %s", exc)
            file_row = await self._files.create(
                user_id=user_id,
                filename=filename,
                content_type=content_type,
                size_bytes=size,
                storage_path=str(path),
                sha256=sha,
            )

        try:
            text = extract_text(content=content, content_type=content_type)
        except TextExtractionError as exc:
            snap = await self._snapshots.create(
                user_id=user_id,
                file_id=file_row.id,
                extracted_text=None,
                parse_status="failed",
            )
            updated = await self._snapshots.update_parse_result(
                snapshot_id=snap.id,
                parse_status="failed",
                parse_error=str(exc),
                extracted_structure=None,
            )
            return updated or snap

        snap = await self._snapshots.create(
            user_id=user_id,
            file_id=file_row.id,
            extracted_text=text,
            parse_status="parsing",
        )

        try:
            payload = await structure_cv(ai_provider=self._ai, extracted_text=text)
        except Exception as exc:
            logger.exception("LinkedIn structuring failed for snapshot %s", snap.id)
            updated = await self._snapshots.update_parse_result(
                snapshot_id=snap.id,
                parse_status="failed",
                parse_error=f"AI structuring failed: {exc}",
                extracted_structure=None,
            )
            return updated or snap

        try:
            await self._kg.ingest_from_cv(
                user_id=user_id, cv_upload_id=snap.id, payload=payload
            )
        except Exception as exc:
            logger.exception("LinkedIn KG ingest failed for snapshot %s", snap.id)
            updated = await self._snapshots.update_parse_result(
                snapshot_id=snap.id,
                parse_status="failed",
                parse_error=f"Graph ingest failed: {exc}",
                extracted_structure=to_dict(payload),
            )
            return updated or snap

        updated = await self._snapshots.update_parse_result(
            snapshot_id=snap.id,
            parse_status="parsed",
            parse_error=None,
            extracted_structure=to_dict(payload),
        )
        return updated or snap
