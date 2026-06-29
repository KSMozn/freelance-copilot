from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ProposalToneLiteral = Literal[
    "pragmatic", "technical_deep", "executive", "consultative", "empathetic"
]


class PersonaArchetypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    description: str
    default_weights: dict[str, int]
    default_skill_category_weights: dict[str, float]
    default_proposal_tone: ProposalToneLiteral
    default_target_roles: list[str]
    default_seniority_band: str | None
    sort_order: int


class PersonaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    archetype_id: UUID
    name: str
    target_role: str | None = None
    target_seniority: str | None = None
    weights: dict[str, int] = Field(default_factory=dict)
    skill_category_weights: dict[str, float] = Field(default_factory=dict)
    proposal_tone: ProposalToneLiteral | None = None
    strategic_priorities: list[str] = Field(default_factory=list)
    pinned_experience_ids: list[str] = Field(default_factory=list)
    pinned_project_ids: list[str] = Field(default_factory=list)
    pinned_skill_ids: list[str] = Field(default_factory=list)
    accent_color: str | None = None
    is_default: bool = False
    is_archived: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PersonaCreate(BaseModel):
    archetype_slug: str = Field(min_length=1, max_length=64)
    name: str | None = Field(default=None, max_length=120)
    target_role: str | None = Field(default=None, max_length=255)
    is_default: bool = False


class PersonaUpdate(BaseModel):
    """Partial update. Any omitted field is left untouched."""

    name: str | None = Field(default=None, max_length=120)
    target_role: str | None = Field(default=None, max_length=255)
    target_seniority: str | None = Field(default=None, max_length=40)
    weights: dict[str, int] | None = None
    skill_category_weights: dict[str, float] | None = None
    proposal_tone: ProposalToneLiteral | None = None
    strategic_priorities: list[str] | None = None
    pinned_experience_ids: list[str] | None = None
    pinned_project_ids: list[str] | None = None
    pinned_skill_ids: list[str] | None = None
    accent_color: str | None = Field(default=None, max_length=16)
    is_archived: bool | None = None
