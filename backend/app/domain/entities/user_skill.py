from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass(slots=True)
class UserSkillEntry:
    """One row in the per-user skill "pot."

    `sources` is the canonical provenance map. Shape:
        {
          "repo_ids": [<uuid>, ...],
          "resume_ids": [<uuid>, ...],
          "portfolio_ids": [<uuid>, ...],
          "cv_upload_ids": [<uuid>, ...],
          "linkedin_snapshot_ids": [<uuid>, ...],
          "manual": bool,
          "ai_suggested": bool,
        }
    Future ingest paths (CV, LinkedIn) extend this without schema changes.
    """

    id: UUID
    user_id: UUID
    skill_id: UUID
    proficiency: int  # 1..5
    years_experience: Decimal | None
    sources: dict[str, Any] = field(default_factory=dict)
    evidence_count: int = 0
    is_active: bool = True
    pinned: bool = False
    last_evidence_date: datetime | None = None
    added_at: datetime | None = None
    updated_at: datetime | None = None
