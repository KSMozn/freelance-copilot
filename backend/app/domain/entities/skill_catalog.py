from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID

SkillCategory = Literal[
    "language",
    "framework",
    "tool",
    "platform",
    "database",
    "domain",
    "soft",
    "practice",
    "leadership",
]


@dataclass(slots=True)
class SkillCatalogEntry:
    id: UUID
    slug: str
    name: str
    category: SkillCategory
    aliases: list[str] = field(default_factory=list)
    is_system_seeded: bool = False
    created_by_user_id: UUID | None = None
    created_at: datetime | None = None
