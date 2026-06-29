from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID

ProposalTone = Literal[
    "pragmatic", "technical_deep", "executive", "consultative", "empathetic"
]


@dataclass(slots=True)
class PersonaArchetype:
    """System-seeded persona template — immutable from user CRUD."""

    id: UUID
    slug: str
    name: str
    description: str
    default_weights: dict[str, int]
    default_skill_category_weights: dict[str, float]
    default_proposal_tone: ProposalTone
    default_target_roles: list[str]
    default_seniority_band: str | None
    is_active: bool = True
    sort_order: int = 0
    created_at: datetime | None = None


@dataclass(slots=True)
class Persona:
    """A user's instance of an archetype.

    JSONB fields hold overrides on top of archetype defaults. The runtime
    "effective" view is computed in :class:`PersonaProfileResolver` by merging
    persona values with archetype defaults (persona wins).
    """

    id: UUID
    user_id: UUID
    archetype_id: UUID
    name: str
    target_role: str | None = None
    target_seniority: str | None = None
    weights: dict[str, int] = field(default_factory=dict)
    skill_category_weights: dict[str, float] = field(default_factory=dict)
    proposal_tone: ProposalTone | None = None
    strategic_priorities: list[str] = field(default_factory=list)
    pinned_experience_ids: list[str] = field(default_factory=list)
    pinned_project_ids: list[str] = field(default_factory=list)
    pinned_skill_ids: list[str] = field(default_factory=list)
    accent_color: str | None = None
    is_default: bool = False
    is_archived: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
