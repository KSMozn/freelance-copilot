"""Deterministic AI provider used in tests and offline development.

Picks plausible values from the actual job text so downstream services
(scoring, persistence) get exercised on realistic shapes — without calling out
to OpenAI/Anthropic.
"""
from __future__ import annotations

import re
from typing import Any

from app.domain.providers.ai_provider import AIRawResponse


_KNOWN_SKILLS = (
    "Python", "FastAPI", "Django", "Flask", "PostgreSQL", "MySQL", "MongoDB",
    "Docker", "Kubernetes", "AWS", "GCP", "Azure", "React", "TypeScript",
    "JavaScript", "Node.js", "Next.js", "Vue", ".NET", "C++", "C#", "Go",
    "Rust", "Java", "Kotlin", "Swift", "Redis", "Kafka", "RabbitMQ",
    "GraphQL", "REST", "gRPC", "Tailwind", "shadcn", "Vite",
    "OpenAI", "Claude", "LLM", "RAG", "AI", "ML", "TensorFlow", "PyTorch",
)

_KNOWN_DOMAINS = (
    ("AI", "AI SaaS"),
    ("LLM", "AI SaaS"),
    ("document", "Document Management"),
    ("fintech", "FinTech"),
    ("finance", "FinTech"),
    ("government", "Government"),
    ("analytics", "Analytics"),
    ("data platform", "Data Platforms"),
    ("data pipeline", "Data Platforms"),
    ("cloud", "Cloud Platforms"),
    ("saas", "Enterprise SaaS"),
)


def _extract_skills(text: str) -> list[str]:
    found: list[str] = []
    haystack = text.lower()
    for skill in _KNOWN_SKILLS:
        needle = skill.lower()
        # word-boundary-ish match; tolerate adjoining punctuation/spaces
        if re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", haystack):
            found.append(skill)
    return found


def _infer_domain(text: str) -> str | None:
    haystack = text.lower()
    for keyword, label in _KNOWN_DOMAINS:
        if keyword in haystack:
            return label
    return None


def _infer_complexity(text: str) -> str:
    n = len(text)
    if n > 1500:
        return "high"
    if n > 500:
        return "medium"
    return "low"


def _infer_seniority(text: str) -> str:
    lowered = text.lower()
    if any(w in lowered for w in ("staff", "principal", "architect")):
        return "staff"
    if any(w in lowered for w in ("lead", "tech lead", "team lead")):
        return "lead"
    if any(w in lowered for w in ("senior", "sr.", "expert")):
        return "senior"
    if any(w in lowered for w in ("junior", "jr.", "entry")):
        return "junior"
    return "mid"


def _hours_range(complexity: str) -> tuple[int, int]:
    return {"low": (5, 15), "medium": (20, 40), "high": (60, 120)}[complexity]


def _budget_assessment(budget_min: float | None, budget_max: float | None) -> str:
    if budget_min is None and budget_max is None:
        return "unclear"
    top = budget_max or budget_min or 0
    if top >= 3000:
        return "high"
    if top >= 800:
        return "reasonable"
    return "low"


def _build_payload(
    *,
    title: str,
    description: str,
    budget_min: float | None,
    budget_max: float | None,
    proposal_count: int | None,
) -> dict[str, Any]:
    text = f"{title}\n{description}"
    skills = _extract_skills(text) or ["Python"]
    complexity = _infer_complexity(text)
    hmin, hmax = _hours_range(complexity)
    domain = _infer_domain(text)
    seniority = _infer_seniority(text)

    red_flags: list[str] = []
    green_flags: list[str] = []
    risks: list[dict[str, str]] = []
    lowered = description.lower()
    if "asap" in lowered or "urgent" in lowered or "tight deadline" in lowered:
        red_flags.append("Tight deadline language ('ASAP'/'urgent')")
        risks.append({
            "risk": "Unrealistic timeline pressure",
            "severity": "medium",
            "mitigation": "Pin down milestones and a realistic end date before bidding.",
        })
    if "long term" in lowered or "ongoing" in lowered:
        green_flags.append("Mentions a long-term / ongoing engagement")
    if skills:
        green_flags.append(f"Tech stack is clear ({', '.join(skills[:3])}…)")
    if proposal_count is not None and proposal_count >= 30:
        red_flags.append(f"High competition ({proposal_count} proposals)")
    if "scope" not in lowered and "deliverable" not in lowered:
        risks.append({
            "risk": "Scope and deliverables are not explicit",
            "severity": "medium",
            "mitigation": "Request a written acceptance-criteria list before accepting.",
        })

    risk_level = "high" if red_flags else "medium" if risks else "low"

    return {
        "summary": (
            f"{seniority.capitalize()}-level engagement around {', '.join(skills[:3])}. "
            f"{complexity.capitalize()} complexity; estimated {hmin}–{hmax} hours."
        ),
        "required_skills": skills[: max(3, len(skills) // 2)] or skills,
        "preferred_skills": skills[len(skills) // 2 :] if len(skills) > 1 else [],
        "technologies": skills,
        "business_domain": domain,
        "seniority_level": seniority,
        "complexity": complexity,
        "estimated_hours_min": hmin,
        "estimated_hours_max": hmax,
        "budget_assessment": _budget_assessment(budget_min, budget_max),
        "client_intent": "Build / improve a working system as described in the post.",
        "hidden_requirements": [
            "Should be able to work independently with light oversight.",
        ],
        "deliverables": ["Working code per the description", "Brief deployment / handover notes"],
        "risks": risks,
        "red_flags": red_flags,
        "green_flags": green_flags,
        "questions_to_ask_client": [
            "What does 'done' look like — is there an acceptance-criteria list?",
            "What is the expected timeline and is there flexibility?",
        ],
        "risk_level": risk_level,
        "communication_required": "Async-first, with one short weekly sync.",
    }


class MockAIProvider:
    """Heuristic provider that synthesizes a plausible analysis from the input text."""

    name = "mock"

    def __init__(self, model: str = "mock-deterministic-v1") -> None:
        self.model = model

    async def analyze_job(
        self,
        *,
        system_prompt: str,  # noqa: ARG002 -- accepted for protocol compatibility
        user_prompt: str,
    ) -> AIRawResponse:
        title = _extract_field(user_prompt, "Title:") or ""
        budget = _extract_field(user_prompt, "Budget:") or ""
        proposals_text = _extract_field(user_prompt, "Proposals so far:") or ""
        description = _extract_block(
            user_prompt, "--- JOB DESCRIPTION ---", "--- END ---"
        )

        budget_min, budget_max = _parse_budget(budget)
        try:
            proposal_count = int(proposals_text)
        except (TypeError, ValueError):
            proposal_count = None

        data = _build_payload(
            title=title,
            description=description,
            budget_min=budget_min,
            budget_max=budget_max,
            proposal_count=proposal_count,
        )
        return AIRawResponse(data=data, provider=self.name, model=self.model)


def _extract_field(text: str, label: str) -> str | None:
    for line in text.splitlines():
        if line.startswith(label):
            return line[len(label) :].strip()
    return None


def _extract_block(text: str, start: str, end: str) -> str:
    try:
        a = text.index(start) + len(start)
        b = text.index(end, a)
    except ValueError:
        return text
    return text[a:b].strip()


def _parse_budget(budget: str) -> tuple[float | None, float | None]:
    numbers = [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", budget)]
    if not numbers:
        return None, None
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    return min(numbers), max(numbers)
