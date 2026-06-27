from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class Portfolio:
    """Pure domain representation of a portfolio project."""

    id: UUID
    user_id: UUID
    title: str
    long_description: str
    short_description: str | None
    role: str | None
    business_domain: str | None
    github_url: str | None
    live_url: str | None
    technologies: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)
    highlight: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def embedding_text(self) -> str:
        """Concatenated text used to build the portfolio's embedding.

        Order is deterministic so the mock provider's output stays stable
        across re-embeds, and so test snapshots remain meaningful.
        """
        parts: list[str] = [self.title]
        if self.short_description:
            parts.append(self.short_description)
        parts.append(self.long_description)
        if self.role:
            parts.append(f"Role: {self.role}")
        if self.business_domain:
            parts.append(f"Domain: {self.business_domain}")
        if self.technologies:
            parts.append("Technologies: " + ", ".join(self.technologies))
        if self.skills:
            parts.append("Skills: " + ", ".join(self.skills))
        if self.features:
            parts.append("Features: " + " · ".join(self.features))
        if self.outcomes:
            parts.append("Outcomes: " + " · ".join(self.outcomes))
        return "\n".join(parts)
