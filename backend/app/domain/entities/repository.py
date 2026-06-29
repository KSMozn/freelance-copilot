from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class StarStory:
    """Interview-ready Situation / Task / Action / Result story for a repo.

    `headline` is the one-line hook proposals can lead with — STAR fields are
    the deeper bullets used in interview prep.
    """

    headline: str
    situation: str
    task: str
    action: str
    result: str


@dataclass(slots=True)
class Repository:
    """A user's GitHub code repository, scanned for technical evidence.

    Distinct from `Portfolio` (which is hand-curated story-telling) — this is
    mechanically extracted metadata used for skill / stack matching.
    """

    id: UUID
    user_id: UUID
    github_url: str
    owner: str
    name: str
    default_branch: str | None
    description: str | None
    languages: dict[str, int]
    frameworks: list[str]
    libraries: list[str]
    databases: list[str]
    authentication: list[str]
    ai_providers: list[str]
    cloud: list[str]
    ci_systems: list[str]
    test_frameworks: list[str]
    has_docker: bool
    has_ci: bool
    has_tests: bool
    architecture_summary: str | None
    business_domain: str | None
    strengths: list[str]
    highlights: list[str]
    readme_excerpt: str | None
    scan_status: str  # 'pending' | 'scanned' | 'failed'
    scan_error: str | None
    scanned_at: datetime | None = None
    star_story: StarStory | None = None
    path_index: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    skills: list[str] = field(default_factory=list)  # derived: union of frameworks+libs+db+auth+ai+cloud

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.name}"

    def derived_skills(self) -> list[str]:
        """Union of every detected stack signal — what the matcher compares
        against the job's required skills.
        """
        out: list[str] = []
        seen: set[str] = set()
        for src in (
            list(self.languages.keys()),
            self.frameworks,
            self.libraries,
            self.databases,
            self.authentication,
            self.ai_providers,
            self.cloud,
            self.ci_systems,
            self.test_frameworks,
        ):
            for item in src:
                key = item.strip().lower()
                if key and key not in seen:
                    seen.add(key)
                    out.append(item)
        return out

    def embedding_text(self) -> str:
        parts: list[str] = [f"{self.owner}/{self.name}"]
        if self.description:
            parts.append(self.description)
        if self.architecture_summary:
            parts.append(self.architecture_summary)
        if self.business_domain:
            parts.append(f"Domain: {self.business_domain}")
        if self.languages:
            parts.append("Languages: " + ", ".join(self.languages.keys()))
        if self.frameworks:
            parts.append("Frameworks: " + ", ".join(self.frameworks))
        if self.libraries:
            parts.append("Libraries: " + ", ".join(self.libraries))
        if self.databases:
            parts.append("Databases: " + ", ".join(self.databases))
        if self.authentication:
            parts.append("Authentication: " + ", ".join(self.authentication))
        if self.ai_providers:
            parts.append("AI providers: " + ", ".join(self.ai_providers))
        if self.cloud:
            parts.append("Cloud: " + ", ".join(self.cloud))
        if self.ci_systems:
            parts.append("CI: " + ", ".join(self.ci_systems))
        if self.test_frameworks:
            parts.append("Testing: " + ", ".join(self.test_frameworks))
        if self.strengths:
            parts.append("Strengths: " + " · ".join(self.strengths))
        if self.highlights:
            parts.append("Highlights: " + " · ".join(self.highlights))
        if self.readme_excerpt:
            parts.append(self.readme_excerpt)
        return "\n".join(parts)
