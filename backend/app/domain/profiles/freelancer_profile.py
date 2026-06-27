from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class FreelancerProfile:
    """Static description of what the freelancer is strong at.

    Lives in the domain layer because scoring rules consume it. The default
    instance below seeds Phase-2 behaviour; later phases will load a per-user
    profile from the database without changing any scoring code.
    """

    version: str
    strong_skills: tuple[str, ...]
    strong_domains: tuple[str, ...]
    strategic_priorities: tuple[str, ...]
    weights: dict[str, int] = field(default_factory=dict)


DEFAULT_FREELANCER_PROFILE = FreelancerProfile(
    version="default-v1",
    strong_skills=(
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
        "Kubernetes",
        "React",
        "TypeScript",
        "Node.js",
        ".NET",
        "C++",
        "AI",
        "LLM",
        "RAG",
        "OpenAI",
        "Claude",
    ),
    strong_domains=(
        "AI SaaS",
        "Enterprise SaaS",
        "Document Management",
        "Government",
        "FinTech",
        "Analytics",
        "Data Platforms",
        "Cloud Platforms",
    ),
    strategic_priorities=(
        "AI implementation",
        "architecture review",
        "technical audit",
        "backend API",
        "data processing",
        "RAG",
        "automation",
    ),
    weights={
        "technical_fit": 25,
        "domain_fit": 10,
        "proposal_count": 20,
        "budget_attractiveness": 10,
        "client_quality": 10,
        "estimated_effort": 10,
        "risk_level": 10,
        "strategic_value": 5,
    },
)
