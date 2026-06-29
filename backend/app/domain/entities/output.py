from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

OutputKind = Literal[
    "upwork_proposal",
    "cover_letter",
    "recruiter_reply",
    "linkedin_message",
    "consulting_proposal",
    "screening_answer",
    "resume_tailored",
]

EvidenceType = Literal[
    "experience", "project", "repository", "certificate", "content_item", "skill"
]


@dataclass(slots=True)
class Citation:
    """A claim in the generated body backed by a graph node.

    `snippet` is the substring from the body that triggered the citation,
    so the UI can highlight it. `evidence_label` is the human-readable
    name of the cited node (e.g. "Acme Corp — Senior Backend Engineer").
    """

    claim: str
    evidence_type: EvidenceType
    evidence_id: str | None
    evidence_label: str
    snippet: str | None = None


@dataclass(slots=True)
class Output:
    id: UUID
    user_id: UUID
    persona_id: UUID | None
    job_id: UUID | None
    kind: OutputKind
    title: str | None
    content_markdown: str
    content_html: str | None = None
    citations: list[Citation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    tone: str | None = None
    ai_provider: str | None = None
    ai_model: str | None = None
    created_at: datetime | None = None
