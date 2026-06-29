from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class Resume:
    """Pure domain representation of a structured resume profile.

    No file URL, no PDF — Phase 4 stores the structured profile only.
    """

    id: UUID
    user_id: UUID
    title: str
    target_role: str | None
    summary: str | None
    seniority_level: str | None
    primary_skills: list[str] = field(default_factory=list)
    secondary_skills: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)
    project_highlights: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def embedding_text(self) -> str:
        """Concatenated text that becomes the resume's embedding source.

        Order is deterministic so the mock provider stays stable across
        re-embeds.
        """
        parts: list[str] = [self.title]
        if self.target_role:
            parts.append(f"Target role: {self.target_role}")
        if self.summary:
            parts.append(self.summary)
        if self.seniority_level:
            parts.append(f"Seniority: {self.seniority_level}")
        if self.primary_skills:
            parts.append("Primary skills: " + ", ".join(self.primary_skills))
        if self.secondary_skills:
            parts.append("Secondary skills: " + ", ".join(self.secondary_skills))
        if self.domains:
            parts.append("Domains: " + ", ".join(self.domains))
        if self.industries:
            parts.append("Industries: " + ", ".join(self.industries))
        if self.achievements:
            parts.append("Achievements: " + " · ".join(self.achievements))
        if self.project_highlights:
            parts.append("Project highlights: " + " · ".join(self.project_highlights))
        if self.keywords:
            parts.append("Keywords: " + ", ".join(self.keywords))
        return "\n".join(parts)
