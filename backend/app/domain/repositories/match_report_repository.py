from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.match_report import MatchReport


class MatchReportRepository(Protocol):
    async def list_for_job(
        self, *, user_id: UUID, job_id: UUID
    ) -> list[MatchReport]: ...

    async def get_for_pair(
        self, *, user_id: UUID, job_id: UUID, persona_id: UUID | None
    ) -> MatchReport | None: ...

    async def upsert(self, report: MatchReport, *, payload: dict[str, Any]) -> MatchReport:
        """Insert-or-update keyed by (job_id, persona_id).

        `payload` carries the structured fields so the implementation can
        serialise nested dataclasses (GapRecommendation) into JSONB cleanly.
        """
        ...
