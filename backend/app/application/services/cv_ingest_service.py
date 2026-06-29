"""CvIngestService — accept an upload, extract text, structure, ingest into the graph.

The pipeline (sync end-to-end for Phase D MVP):

  1. sha256 the bytes → dedup: if we've seen this file from this user before,
     return the existing parsed row.
  2. Write the blob to local disk under ``var/uploads/<sha256>`` (mounted
     via the docker-compose bind mount, so files survive container restarts).
  3. Extract text (pdfminer.six for PDF, python-docx for DOCX, passthrough
     for pasted text).
  4. Insert a ``cv_uploads`` row with ``parse_status='parsing'``.
  5. Call ``structure_cv`` to produce a strict-JSON CV structure.
  6. Hand the structured payload to ``KnowledgeGraphService.ingest_from_cv``
     so experiences land in the graph and skills land in the pot.
  7. Flip ``parse_status='parsed'`` and persist the structured JSON + skill
     list back onto the upload row.

Failures at any step short-circuit to ``parse_status='failed'`` with a
human-readable ``parse_error``. The upload row is preserved either way so
operators can debug.
"""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from uuid import UUID

from app.application.services.cv_structuring import (
    CvStructuredPayload,
    structure_cv,
    to_dict,
)
from app.application.services.knowledge_graph_service import KnowledgeGraphService
from app.application.services.text_extraction import (
    TextExtractionError,
    extract_text,
)
from app.domain.entities.ingestion import CvUploadEntry
from app.domain.providers.ai_provider import AIProvider
from app.domain.repositories.ingestion_repositories import CvUploadRepository

logger = logging.getLogger(__name__)

UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", "var/uploads"))


class CvIngestService:
    def __init__(
        self,
        *,
        cv_uploads: CvUploadRepository,
        ai_provider: AIProvider,
        knowledge_graph: KnowledgeGraphService,
        uploads_dir: Path = UPLOADS_DIR,
    ) -> None:
        self._cv_uploads = cv_uploads
        self._ai = ai_provider
        self._kg = knowledge_graph
        self._uploads_dir = uploads_dir

    async def ingest(
        self,
        *,
        user_id: UUID,
        persona_id: UUID | None,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> CvUploadEntry:
        sha = hashlib.sha256(content).hexdigest()
        size = len(content)

        # 1. Dedup by sha — same file from same user already parsed.
        existing = await self._cv_uploads.get_by_sha(user_id=user_id, sha256=sha)
        if existing is not None and existing.parse_status == "parsed":
            return existing

        # 2. Extract text (raises if image-only PDF / unsupported type).
        try:
            text = extract_text(content=content, content_type=content_type)
        except TextExtractionError as exc:
            return await self._record_failure(
                user_id=user_id,
                persona_id=persona_id,
                filename=filename,
                content_type=content_type,
                size=size,
                sha=sha,
                storage_path=None,
                extracted_text=None,
                error=str(exc),
            )

        # 3. Write the blob to disk (best-effort — failure here doesn't block
        #    the rest of the pipeline since the text is already extracted).
        storage_path = self._store_blob(sha=sha, content=content)

        # 4. Create the row.
        cv = await self._cv_uploads.create(
            user_id=user_id,
            persona_id=persona_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size,
            storage_path=storage_path,
            sha256=sha,
            extracted_text=text,
            parse_status="parsing",
        )

        # 5. Structure via LLM. Any failure ⇒ failed row but text is kept.
        try:
            payload = await structure_cv(ai_provider=self._ai, extracted_text=text)
        except Exception as exc:
            logger.exception("CV structuring failed for upload %s", cv.id)
            updated = await self._cv_uploads.update_parse_result(
                cv_id=cv.id,
                parse_status="failed",
                parse_error=f"AI structuring failed: {exc}",
                extracted_structure=None,
                extracted_skills=None,
            )
            return updated or cv

        # 6. Ingest into the knowledge graph.
        try:
            await self._kg.ingest_from_cv(
                user_id=user_id, cv_upload_id=cv.id, payload=payload
            )
        except Exception as exc:
            logger.exception("KG ingest failed for upload %s", cv.id)
            updated = await self._cv_uploads.update_parse_result(
                cv_id=cv.id,
                parse_status="failed",
                parse_error=f"Graph ingest failed: {exc}",
                extracted_structure=to_dict(payload),
                extracted_skills=_skill_names(payload),
            )
            return updated or cv

        # 7. Persist parsed structure + skills onto the row.
        updated = await self._cv_uploads.update_parse_result(
            cv_id=cv.id,
            parse_status="parsed",
            parse_error=None,
            extracted_structure=to_dict(payload),
            extracted_skills=_skill_names(payload),
        )
        return updated or cv

    # ---- helpers ----

    def _store_blob(self, *, sha: str, content: bytes) -> str | None:
        try:
            self._uploads_dir.mkdir(parents=True, exist_ok=True)
            path = self._uploads_dir / sha
            if not path.exists():
                path.write_bytes(content)
            return str(path)
        except OSError as exc:
            logger.warning("Failed to write upload blob: %s", exc)
            return None

    async def _record_failure(
        self,
        *,
        user_id: UUID,
        persona_id: UUID | None,
        filename: str,
        content_type: str,
        size: int,
        sha: str,
        storage_path: str | None,
        extracted_text: str | None,
        error: str,
    ) -> CvUploadEntry:
        # Surface the failure as a persisted row so the UI can show "we
        # tried, here's why it failed."
        existing = await self._cv_uploads.get_by_sha(user_id=user_id, sha256=sha)
        if existing is not None:
            updated = await self._cv_uploads.update_parse_result(
                cv_id=existing.id,
                parse_status="failed",
                parse_error=error,
                extracted_structure=None,
                extracted_skills=None,
            )
            return updated or existing
        return await self._cv_uploads.create(
            user_id=user_id,
            persona_id=persona_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size,
            storage_path=storage_path,
            sha256=sha,
            extracted_text=extracted_text,
            parse_status="failed",
        )


def _skill_names(payload: CvStructuredPayload) -> list[str]:
    """Persisted form of `extracted_skills` JSONB: distinct skill names."""
    from app.application.services.cv_structuring import all_skill_names
    return all_skill_names(payload)
