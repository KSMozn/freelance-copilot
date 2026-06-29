from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

OutputKindLiteral = Literal[
    "upwork_proposal",
    "cover_letter",
    "recruiter_reply",
    "linkedin_message",
    "consulting_proposal",
    "screening_answer",
    "resume_tailored",
]

EvidenceTypeLiteral = Literal[
    "experience", "project", "repository", "certificate", "content_item", "skill"
]


class CitationRead(BaseModel):
    claim: str
    evidence_type: EvidenceTypeLiteral
    evidence_id: str | None = None
    evidence_label: str
    snippet: str | None = None


class OutputRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    persona_id: UUID | None
    job_id: UUID | None
    kind: OutputKindLiteral
    title: str | None
    content_markdown: str
    content_html: str | None
    citations: list[CitationRead] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tone: str | None
    ai_provider: str | None
    ai_model: str | None
    created_at: datetime | None = None


class OutputGenerateRequest(BaseModel):
    kind: OutputKindLiteral
    job_id: UUID | None = None
    persona_id: UUID | None = None
