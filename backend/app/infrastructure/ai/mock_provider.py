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


# Map a skill name to (category, default importance). Kept tight — anything not
# in this table falls into "tech_stack" with importance derived from how
# emphatically it shows up in the post.
_SKILL_CATEGORY: dict[str, tuple[str, int]] = {
    "Python": ("tech_stack", 5),
    "Node.js": ("tech_stack", 5),
    "TypeScript": ("tech_stack", 5),
    "JavaScript": ("tech_stack", 5),
    "Go": ("tech_stack", 5),
    "Rust": ("tech_stack", 4),
    "Java": ("tech_stack", 4),
    "Kotlin": ("tech_stack", 3),
    "Swift": ("tech_stack", 3),
    "C++": ("tech_stack", 4),
    "C#": ("tech_stack", 4),
    ".NET": ("tech_stack", 4),
    "React": ("tech_stack", 5),
    "Next.js": ("tech_stack", 5),
    "Vue": ("tech_stack", 4),
    "FastAPI": ("tech_stack", 5),
    "Django": ("tech_stack", 4),
    "Flask": ("tech_stack", 3),
    "Tailwind": ("tech_stack", 3),
    "shadcn": ("tech_stack", 2),
    "Vite": ("tech_stack", 2),
    "GraphQL": ("architecture", 4),
    "REST": ("architecture", 3),
    "gRPC": ("architecture", 3),
    "PostgreSQL": ("database", 5),
    "MySQL": ("database", 4),
    "MongoDB": ("database", 4),
    "Redis": ("database", 3),
    "Kafka": ("integrations", 3),
    "RabbitMQ": ("integrations", 3),
    "Docker": ("devops", 4),
    "Kubernetes": ("devops", 4),
    "AWS": ("cloud_platform", 5),
    "GCP": ("cloud_platform", 4),
    "Azure": ("cloud_platform", 4),
    "OpenAI": ("ai_llm", 5),
    "Claude": ("ai_llm", 5),
    "LLM": ("ai_llm", 5),
    "RAG": ("ai_llm", 5),
    "AI": ("ai_llm", 4),
    "ML": ("ai_llm", 4),
    "TensorFlow": ("ai_llm", 3),
    "PyTorch": ("ai_llm", 3),
}


def _build_stack_requirements(
    *,
    text: str,
    skills: list[str],
) -> list[dict[str, Any]]:
    """Project detected skills into the structured stack list with 1–5
    importance based on how prominently each appears in the post.
    """
    lowered = text.lower()
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for skill in skills:
        key = skill.lower()
        if key in seen:
            continue
        seen.add(key)
        category, base = _SKILL_CATEGORY.get(skill, ("tech_stack", 3))
        occurrences = lowered.count(key)
        bump = min(2, max(0, occurrences - 1))
        importance = max(1, min(5, base + bump))
        out.append({"category": category, "name": skill, "importance": importance})

    # Implicit signals not in the canonical skill list.
    if "stripe" in lowered:
        out.append({"category": "billing", "name": "Stripe", "importance": 5})
    if "jwt" in lowered or "oauth" in lowered or " auth " in lowered:
        out.append({"category": "authentication", "name": "Authentication / JWT", "importance": 4})
    if "test" in lowered or " ci " in lowered or "ci/cd" in lowered:
        out.append({"category": "testing", "name": "Automated testing", "importance": 3})
    if "deploy" in lowered or "production" in lowered:
        out.append({"category": "deployment", "name": "Production deployment", "importance": 3})
    return out


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
        "stack_requirements": _build_stack_requirements(text=text, skills=skills),
    }


PROPOSAL_MARKER = "--- PROPOSAL ASSIGNMENT ---"
STAR_MARKER = "--- STAR STORY ASSIGNMENT ---"
RESEARCH_MARKER = "--- COMPANY RESEARCH ASSIGNMENT ---"
PORTFOLIO_STORY_MARKER = "--- PORTFOLIO STORY ASSIGNMENT ---"
# Phase D — surfaced from app.application.services.cv_structuring. Kept as a
# duplicate literal here to avoid importing application-layer code from the
# infrastructure layer.
CV_INGEST_MARKER = "CV_INGEST_MARKER"
OUTPUT_MARKER = "OUTPUT_GENERATION"  # Phase F — mirrors output_prompts.OUTPUT_MARKER


def _build_portfolio_story_payload(user_prompt: str) -> dict[str, Any]:
    """Deterministic placeholder lead-with story from portfolio + job context."""
    job_title = _extract_field(user_prompt, "Job title:") or "the project"
    job_domain = _extract_field(user_prompt, "Job domain:") or ""
    portfolio = _extract_field(user_prompt, "Chosen portfolio:") or "a recent project"
    pf_domain = _extract_field(user_prompt, "Portfolio domain:") or ""
    short_desc = _extract_field(user_prompt, "Short description:") or ""
    overlaps = _extract_field(user_prompt, "Overlapping skills:") or ""

    domain_bridge = (
        f"{pf_domain} → {job_domain}" if pf_domain and job_domain else (pf_domain or job_domain)
    )
    overlap_lead = overlaps.split(",")[0].strip() if overlaps else "the stack"

    opener = (
        f"Reading your post, the closest analogue I've shipped is {portfolio} — "
        f"same shape: {overlap_lead} at the core."
    )
    body = (
        f"{short_desc}".strip()
        + (" " if short_desc else "")
        + f"That project sits in the {pf_domain or 'same'} space and uses the "
        f"same kind of tooling you're describing for {job_title}. I'd start by "
        "scoping the smallest end-to-end slice so we de-risk the spec early."
    )
    why = (
        f"Strongest overlap: {domain_bridge or 'shared stack and domain'} — "
        "lines up directly with the job's required skills."
    )
    return {
        "opener": opener[:400],
        "body": body[:800],
        "why_this_fit": why[:400],
    }


def _build_research_payload(user_prompt: str) -> dict[str, Any]:
    """Deterministic company-research placeholder for offline mode.

    Picks signals from the page text the prompt embedded so test snapshots
    are meaningful without a real model call.
    """
    title = _extract_field(user_prompt, "Page title:") or "the product"
    description = _extract_field(user_prompt, "Meta description:") or ""
    body = _extract_block(user_prompt, "Page text:", "\n\nReturn JSON")
    haystack = (title + " " + description + " " + body).lower()

    # Cheap domain inference
    domain = None
    for keyword, label in (
        ("saas", "Enterprise SaaS"),
        ("analytics", "Analytics"),
        ("fintech", "FinTech"),
        ("ai", "AI"),
        ("healthcare", "Healthcare"),
        ("ecommerce", "E-commerce"),
    ):
        if keyword in haystack:
            domain = label
            break

    # Existing-stack inference from page text
    stack: list[str] = []
    for tech in (
        "Next.js", "React", "Vue", "Node.js", "Python", "FastAPI", "Django",
        "PostgreSQL", "MongoDB", "Redis", "AWS", "Vercel", "Stripe", "OpenAI",
    ):
        if tech.lower() in haystack and tech not in stack:
            stack.append(tech)

    funding = None
    for keyword in ("Series A", "Series B", "YC", "Y Combinator", "seed", "pre-seed"):
        if keyword.lower() in haystack:
            funding = f"Mentions {keyword}"
            break

    product_summary = (description or title)[:300] if (description or title) else None
    target_customers = None
    if "b2b" in haystack:
        target_customers = "B2B teams"
    elif "consumer" in haystack:
        target_customers = "Consumer / individuals"

    hook = (
        f"I noticed your product focuses on {domain.lower()} — that's adjacent "
        "to a recent build of mine. [mock provider]"
        if domain
        else f"I noticed you ship {title}. [mock provider]"
    )

    return {
        "business_domain": domain,
        "product_summary": product_summary,
        "target_customers": target_customers,
        "existing_stack": stack[:8],
        "funding_signals": funding,
        "likely_architecture": (
            f"Likely a {stack[0]} app on top of {stack[1]} based on visible cues."
            if len(stack) >= 2
            else None
        ),
        "personalization_hook": hook,
    }


def _build_star_payload(user_prompt: str) -> dict[str, Any]:
    """Deterministic STAR placeholder for offline mode.

    Echoes the repository signals back so test snapshots are meaningful
    without a real model call.
    """
    repo_line = _extract_field(user_prompt, "Repository:") or "the project"
    architecture = _extract_field(user_prompt, "Architecture:") or ""
    domain = _extract_field(user_prompt, "Business domain:") or "the target domain"
    frameworks = _extract_field(user_prompt, "Frameworks:") or ""
    databases = _extract_field(user_prompt, "Databases:") or ""
    ai_providers = _extract_field(user_prompt, "AI providers:") or ""

    stack_parts = [s for s in (frameworks, databases, ai_providers) if s]
    stack = " · ".join(stack_parts) if stack_parts else "a small, focused stack"

    headline = (
        f"Built {repo_line} — a {domain} system on {stack}." if stack_parts
        else f"Built {repo_line} — a focused {domain} engagement."
    )
    situation = (
        f"The team needed a working {domain} system with clear acceptance "
        f"criteria. The codebase shape evidences {stack}."
    )
    task = (
        "Own delivery end-to-end: scope, architecture, implementation, "
        "and a clean hand-over."
    )
    action_bits = []
    if architecture:
        action_bits.append(architecture[:140])
    if frameworks:
        action_bits.append(f"Implemented the core in {frameworks}")
    if databases:
        action_bits.append(f"Persisted state in {databases}")
    if ai_providers:
        action_bits.append(f"Integrated {ai_providers}")
    action = (
        ". ".join(action_bits) + "."
        if action_bits
        else "Shipped the smallest valuable vertical slice first, then layered integrations."
    )
    result = (
        f"Repository scanned cleanly — production-grade signals present "
        f"({domain}). [mock provider]"
    )
    return {
        "headline": headline[:160],
        "situation": situation[:400],
        "task": task[:400],
        "action": action[:600],
        "result": result[:400],
    }


class MockAIProvider:
    """Heuristic provider that synthesizes a plausible JSON response from the prompt.

    Routes by inspecting the user prompt:
    - If `--- PROPOSAL ASSIGNMENT ---` is present, returns a proposal payload.
    - Otherwise returns the analyzer payload (Phase-2 default).
    """

    name = "mock"

    def __init__(self, model: str = "mock-deterministic-v1") -> None:
        self.model = model

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> AIRawResponse:
        if RESEARCH_MARKER in user_prompt:
            data = _build_research_payload(user_prompt)
        elif PORTFOLIO_STORY_MARKER in user_prompt:
            data = _build_portfolio_story_payload(user_prompt)
        elif STAR_MARKER in user_prompt:
            data = _build_star_payload(user_prompt)
        elif PROPOSAL_MARKER in user_prompt:
            data = _build_proposal_payload(user_prompt)
        elif CV_INGEST_MARKER in user_prompt:
            data = _build_cv_ingest_payload(user_prompt)
        elif OUTPUT_MARKER in user_prompt:
            data = _build_output_payload(user_prompt)
        else:
            data = _build_analyzer_payload(user_prompt)
        return AIRawResponse(data=data, provider=self.name, model=self.model)

    async def complete_json_with_image(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_bytes: bytes,
        image_mime_type: str,
    ) -> AIRawResponse:
        """Deterministic placeholder for image-input flows.

        The mock provider cannot actually inspect the screenshot. We return a
        clearly-labeled placeholder so the import pipeline + persistence still
        get exercised end-to-end; switch to AI_PROVIDER=openai|claude for the
        real extraction.
        """
        # A tiny, byte-stable fingerprint helps tests assert the same image
        # produces the same mock payload without surfacing raw bytes.
        fingerprint = (sum(image_bytes) % 1_000_000) if image_bytes else 0
        data = {
            "title": "Imported job (mock provider — switch to OpenAI/Claude for real extraction)",
            "description": (
                "This is a placeholder job created by the mock AI provider. "
                "The actual screenshot was not analyzed because EMBEDDING/AI "
                "provider is set to 'mock'. Set AI_PROVIDER=openai or claude "
                "and supply a key to extract real fields from the image."
            ),
            "source_url": None,
            "budget_type": "hourly",
            "budget_min": 25.0,
            "budget_max": 47.0,
            "currency": "USD",
            "proposal_count": None,
            "project_duration": "1 to 3 months",
            "project_type": "Ongoing project",
            "experience_level": "Expert",
            "location": "Worldwide",
            "posted_at": "—",
            "mandatory_skills": ["JavaScript", "HTML5"],
            "nice_to_have_skills": ["PHP", ".NET Framework"],
            "questions": [
                "Describe the most complex production system you've audited or architected.",
                "Describe your recent experience with similar projects.",
                "Include a link to your GitHub profile and/or website.",
            ],
            "_mock_fingerprint": fingerprint,
        }
        return AIRawResponse(data=data, provider=self.name, model=self.model)


def _build_analyzer_payload(user_prompt: str) -> dict[str, Any]:
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

    return _build_payload(
        title=title,
        description=description,
        budget_min=budget_min,
        budget_max=budget_max,
        proposal_count=proposal_count,
    )


def _build_proposal_payload(user_prompt: str) -> dict[str, Any]:
    """Parse the proposal-context prompt and return a plausible proposal JSON.

    The prompt structure is defined by `proposal_prompts.build_user_prompt`. We
    re-extract a small set of fields here so the mock's output references the
    job, the top portfolio, and the recommended resume — enough to make the
    quality-review path interesting in tests.
    """
    title = _extract_field(user_prompt, "Title:") or "the project"

    # First "1. <title>" line in the portfolio section.
    portfolio_block = _extract_block(
        user_prompt, "--- PORTFOLIO MATCHES ---", "--- "
    )
    top_portfolio = ""
    for line in portfolio_block.splitlines():
        stripped = line.strip()
        if stripped.startswith("1.") or stripped.startswith("1)"):
            top_portfolio = stripped.lstrip("1.)").strip()
            # strip a trailing "(domain)" if present
            if " (" in top_portfolio:
                top_portfolio = top_portfolio.split(" (", 1)[0]
            break

    # First skill list from the resume block.
    resume_block = _extract_block(
        user_prompt, "--- RECOMMENDED RESUME ---", "--- "
    )
    skills_line = ""
    for line in resume_block.splitlines():
        if line.startswith("Primary skills:"):
            skills_line = line[len("Primary skills:") :].strip()
            break
    top_skills = [s.strip() for s in skills_line.split(",") if s.strip()][:3] or [
        "Python",
        "FastAPI",
    ]

    missing_line = ""
    for line in resume_block.splitlines():
        if line.startswith("Missing or weak skills:"):
            missing_line = line[len("Missing or weak skills:") :].strip()
            break
    missing_skills = [s.strip() for s in missing_line.split(",") if s.strip()]

    risks_block = _extract_block(user_prompt, "Risks:", "\n\n")
    first_risk = ""
    for line in risks_block.splitlines():
        stripped = line.strip().lstrip("-").strip()
        if stripped and stripped != "Risks:":
            first_risk = stripped
            break

    skills_phrase = ", ".join(top_skills)
    portfolio_clause = (
        f' I recently shipped "{top_portfolio}", which lines up with what you need.'
        if top_portfolio
        else ""
    )
    body = (
        f"Reading your post, the core ask is a tightly-scoped {skills_phrase} build "
        f"with clear acceptance criteria.{portfolio_clause} "
        "I'd start by locking down the acceptance criteria and the smallest end-to-end "
        "vertical slice — that way we have working software you can demo by the end of "
        "week one, and we surface any scope ambiguity before they become rework. "
        "From there I'd layer in the harder integration bits and keep the test suite "
        "honest so we're not deploying on a hope.\n\n"
        "Two things I'd flag up front: I want to confirm the acceptance criteria for "
        "milestone hand-off, and I'd ask for read-only access to a representative data "
        "sample before quoting fixed-price work. "
    )
    if missing_skills:
        body += (
            f"On the stack: {', '.join(missing_skills[:2])} isn't where I've spent the "
            "most time recently — happy to talk through that on a call. "
        )
    body += "Open to a 20-minute call this week to align on scope; here's my calendar."

    short_body = (
        f"Quick read of the brief: looks like a focused {skills_phrase} build."
        f"{portfolio_clause} "
        "I'd start with a thin end-to-end slice in week one to de-risk scope, then "
        "layer integrations on top. Two things I'd want to clarify before quoting "
        "fixed price: acceptance criteria per milestone, and a small data sample. "
        "Happy to do a 20-minute call this week."
    )

    questions = [
        "What does done look like — is there an acceptance-criteria list per milestone?",
        f"Could you share a representative sample of {top_skills[0]} input/output for sizing?",
        "Is the timeline driven by an external deadline, or is there room to adjust scope?",
    ]
    milestones = [
        {
            "name": "Discovery & acceptance criteria",
            "description": "Lock acceptance criteria, agree on the smallest end-to-end slice, set up the repo.",
            "estimated_hours": 4,
        },
        {
            "name": "Thin vertical slice",
            "description": f"Working end-to-end demo using {skills_phrase} — no integrations yet.",
            "estimated_hours": 12,
        },
        {
            "name": "Integrations & hardening",
            "description": "Layer in the harder integrations, tests, and a deployment guide.",
            "estimated_hours": 16,
        },
        {
            "name": "Hand-over",
            "description": "Walkthrough, written hand-over, and a 30-day fix-it window.",
            "estimated_hours": 2,
        },
    ]
    delivery_approach = [
        "Discovery call to lock acceptance criteria and the smallest viable slice.",
        "Build the thin end-to-end vertical slice first so scope ambiguity surfaces early.",
        "Layer the harder integrations, keep CI green on every push.",
        "Hand-over with a written runbook and a 30-day support window.",
    ]
    risk_notes: list[str] = []
    if first_risk:
        risk_notes.append(first_risk)
    risk_notes.append(
        "Clarify acceptance criteria before committing to a fixed price."
    )
    if missing_skills:
        risk_notes.append(
            "Be explicit on a call about which parts of the stack are newer to me."
        )

    proposal_title = f"Re: {title} — concrete plan and a few clarifying questions"
    strategy = _pick_proposal_strategy(
        user_prompt=user_prompt, top_skills=top_skills, top_portfolio=top_portfolio
    )
    implementation_plan = _build_implementation_plan(
        user_prompt=user_prompt, top_skills=top_skills, strategy=strategy
    )
    diagrams = _build_diagrams(user_prompt=user_prompt, top_skills=top_skills)
    return {
        "strategy": strategy,
        "title": proposal_title,
        "body": body,
        "short_body": short_body,
        "questions": questions,
        "milestones": milestones,
        "delivery_approach": delivery_approach,
        "risk_notes": risk_notes,
        "implementation_plan": implementation_plan,
        "diagrams": diagrams,
    }


def _sanitize_node(label: str) -> str:
    """Strip Mermaid-unfriendly characters from a label."""
    cleaned = re.sub(r"[\[\](){}\"'`]", "", label)
    return cleaned.strip() or "Component"


def _build_diagrams(*, user_prompt: str, top_skills: list[str]) -> list[dict[str, Any]]:
    """Synthesize two Mermaid diagrams: a system flowchart + a sequence flow.

    Heuristic only — picks frontend / backend / db / cache / ai-provider /
    billing nodes from prompt signals. Real OpenAI / Claude providers will
    emit much better diagrams.
    """
    haystack = user_prompt.lower()
    has_react = any(s in haystack for s in ("react", "next.js", "vue", "frontend"))
    has_ai = any(s in haystack for s in ("openai", "claude", "llm", "rag", " ai "))
    has_billing = any(s in haystack for s in ("stripe", "billing", "subscription"))
    has_cache = "redis" in haystack
    db = "PostgreSQL" if "postgres" in haystack or "pgvector" in haystack else (
        "MongoDB" if "mongo" in haystack else "Database"
    )
    api_label = top_skills[0] if top_skills else "API"

    # --- system flowchart ---
    flow_lines: list[str] = ["flowchart TD"]
    flow_lines.append("  Client[Web client]" if has_react else "  Client[Client]")
    flow_lines.append(f"  API[{_sanitize_node(api_label)} API]")
    flow_lines.append(f"  DB[({_sanitize_node(db)})]")
    flow_lines.append("  Client --> API")
    flow_lines.append("  API --> DB")
    if has_cache:
        flow_lines.append("  Cache[(Redis)]")
        flow_lines.append("  API --> Cache")
    if has_ai:
        flow_lines.append("  LLM[LLM provider]")
        flow_lines.append("  API --> LLM")
    if has_billing:
        flow_lines.append("  Stripe[Stripe]")
        flow_lines.append("  API --> Stripe")
        flow_lines.append("  Stripe -.webhook.-> API")
    system_diagram = "\n".join(flow_lines)

    # --- sequence diagram ---
    seq_lines: list[str] = ["sequenceDiagram"]
    seq_lines.append("  participant U as User")
    seq_lines.append("  participant API")
    seq_lines.append(f"  participant DB as {_sanitize_node(db)}")
    if has_ai:
        seq_lines.append("  participant LLM")
    seq_lines.append("  U->>API: Request")
    seq_lines.append("  API->>DB: Load context")
    seq_lines.append("  DB-->>API: Rows")
    if has_ai:
        seq_lines.append("  API->>LLM: Prompt + context")
        seq_lines.append("  LLM-->>API: Structured JSON")
    seq_lines.append("  API-->>U: Response")
    sequence_diagram = "\n".join(seq_lines)

    return [
        {
            "kind": "system",
            "title": "System overview",
            "mermaid": system_diagram,
        },
        {
            "kind": "sequence",
            "title": "Critical request flow",
            "mermaid": sequence_diagram,
        },
    ]


def _build_implementation_plan(
    *,
    user_prompt: str,
    top_skills: list[str],
    strategy: dict[str, Any],
) -> list[dict[str, Any]]:
    """Cheap heuristic week-by-week plan.

    Week 1 is always the thin end-to-end slice (per the prompt rules). Weeks
    2+ light up based on signals in the post — auth, billing, AI, admin —
    falling through to a generic hardening week at the end.
    """
    haystack = user_prompt.lower()
    head_skill = top_skills[0] if top_skills else "the stack"

    plan: list[dict[str, Any]] = [
        {
            "week": 1,
            "focus": "Vertical slice",
            "summary": (
                f"Stand up a working end-to-end {head_skill} demo against a thin "
                "scope so we surface ambiguity early."
            ),
            "deliverables": [
                "Skeleton repo with CI green",
                f"End-to-end {head_skill} happy path",
                "Acceptance-criteria doc",
            ],
        }
    ]
    next_week = 2

    def _add(focus: str, summary: str, deliverables: list[str]) -> None:
        nonlocal next_week
        plan.append(
            {
                "week": next_week,
                "focus": focus,
                "summary": summary,
                "deliverables": deliverables,
            }
        )
        next_week += 1

    if any(t in haystack for t in ("auth", "jwt", "oauth", "login")):
        _add(
            "Authentication",
            "Implement authentication + session handling end-to-end.",
            ["JWT login / refresh", "Protected routes", "Sign-up + reset flows"],
        )
    if "stripe" in haystack or "billing" in haystack or "subscription" in haystack:
        _add(
            "Billing",
            "Wire Stripe billing with idempotent webhook handling.",
            ["Plans + checkout", "Webhook processor with retries", "Customer portal"],
        )
    if strategy.get("angle") == "ai" or any(
        t in haystack for t in ("openai", "anthropic", "claude", "llm", "rag", " ai ")
    ):
        _add(
            "AI integration",
            "Layer the LLM provider behind a clean abstraction with evals.",
            ["Provider abstraction", "Prompt + schema validation", "Eval harness"],
        )
    if "admin" in haystack or "dashboard" in haystack:
        _add(
            "Admin UI",
            "Add the internal admin surface for support / oversight.",
            ["Admin auth + roles", "Core admin tables", "Read-only audit view"],
        )

    # Penultimate: deployment, last: hardening. Always present so the plan
    # ends with the production-readiness story.
    _add(
        "Deployment",
        "Set up the production deployment pipeline with rollbacks.",
        ["Dockerfile + compose", "CI deploy on main", "Observability baseline"],
    )
    _add(
        "Hardening",
        "Final pass: edge cases, performance, security review, hand-over.",
        ["Test coverage on critical paths", "Security review notes", "Runbook + hand-over"],
    )

    # Cap to 6 weeks per the prompt rule.
    return plan[:6]


def _pick_proposal_strategy(
    *, user_prompt: str, top_skills: list[str], top_portfolio: str
) -> dict[str, Any]:
    """Heuristic angle selection for the mock provider.

    Order of precedence (first match wins):
      ai > architecture > leadership > fast_delivery > enterprise
      > startup_mindset > hands_on_coding
    """
    haystack = user_prompt.lower()
    skills_lc = {s.lower() for s in top_skills}
    ai_signals = {"openai", "claude", "llm", "rag", "ai", "ml"}
    if skills_lc & ai_signals or any(t in haystack for t in (" ai ", "llm", "rag", "openai", "anthropic")):
        return {
            "angle": "ai",
            "rationale": "Job centers on AI/LLM functionality — lead with concrete RAG / prompt-evaluation experience.",
            "emphasis_points": [
                "Cite the most relevant AI project shipped (evals, RAG, agents)",
                "Show how you'd ground outputs and guardrail hallucinations",
                "Offer to share an eval harness or trace from a past build",
            ],
        }
    if any(t in haystack for t in ("architect", "audit", "scal", "design review")):
        return {
            "angle": "architecture",
            "rationale": "Job emphasizes system design, scale, or audit — lead with architectural framing.",
            "emphasis_points": [
                "Sketch the smallest viable architecture before quoting price",
                "Identify two failure modes the current shape implies",
                "Offer a 1-page architecture write-up as the first milestone",
            ],
        }
    if any(t in haystack for t in ("team", "lead", "manage", "mentor", "stakeholder")):
        return {
            "angle": "leadership",
            "rationale": "Job asks for team or stakeholder ownership — lead with delivery-ownership framing.",
            "emphasis_points": [
                "Reference one engagement where you owned scope + delivery",
                "Describe your weekly stakeholder cadence",
                "Offer a kickoff doc as the first milestone",
            ],
        }
    if any(t in haystack for t in ("asap", "urgent", "this week", "mvp", "tight timeline")):
        return {
            "angle": "fast_delivery",
            "rationale": "Timeline language is tight — lead with a thin vertical slice in week one.",
            "emphasis_points": [
                "Promise a working end-to-end demo by end of week one",
                "Cut scope to the smallest valuable slice up front",
                "Defer integrations to later milestones",
            ],
        }
    if any(t in haystack for t in ("enterprise", "compliance", "soc 2", "hipaa", "audit log")):
        return {
            "angle": "enterprise",
            "rationale": "Enterprise / compliance signals in the post — lead with rigor and integration experience.",
            "emphasis_points": [
                "Reference an enterprise-shaped engagement (compliance / audit)",
                "Call out auth, audit logs, and tenant isolation up front",
                "Offer a written security write-up as a milestone",
            ],
        }
    if any(t in haystack for t in ("founder", "early stage", "stealth", "0 to 1", "first hire")):
        return {
            "angle": "startup_mindset",
            "rationale": "Early-stage post with ambiguous scope — lead with founder-aligned framing.",
            "emphasis_points": [
                "Frame the engagement as iterative product discovery",
                "Offer optionality on scope cuts vs. scope adds",
                "Bias toward shipping over speccing",
            ],
        }
    head_skill = top_skills[0] if top_skills else "the stack"
    return {
        "angle": "hands_on_coding",
        "rationale": f"Builder-shaped job around {head_skill} — lead with hands-on shipping cadence.",
        "emphasis_points": [
            "Reference the most relevant repo / portfolio entry",
            "Propose a thin end-to-end slice in week one",
            "Be explicit about test + deployment posture",
        ],
    }


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


# ----------------------- Phase D — CV structuring -----------------------


def _build_cv_ingest_payload(user_prompt: str) -> dict[str, Any]:
    """Heuristic CV → structured-JSON for dev / offline runs.

    Detects experience blocks via simple ``Company`` / ``Role`` / date
    patterns. Doesn't try to be clever — the real extraction happens with a
    real LLM in production; this just gives us a deterministic shape so the
    CvIngestService + KG ingest path is exercisable without network calls.
    """
    text = user_prompt
    # Strip the marker preamble so we don't pick "CV" out of it.
    text = text.split("\n\n", 2)[-1] if "\n\n" in text else text

    skills = _extract_skills_from_text(text)
    experiences = _extract_experiences_from_text(text)

    summary = ""
    for line in text.splitlines():
        stripped = line.strip()
        if 60 < len(stripped) < 300 and stripped.endswith(("." , "!", "?")):
            summary = stripped
            break

    return {
        "summary": summary or "Experienced engineer.",
        "experiences": experiences,
        "skills": skills,
    }


_KNOWN_SKILLS = {
    "Python", "TypeScript", "JavaScript", "Go", "Rust", "Java", "Kotlin",
    "FastAPI", "Django", "Flask", "Express", "NestJS", "Next.js", "React",
    "Vue", "Angular", "Svelte", "Spring", "Rails", "Laravel",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "ClickHouse",
    "Cassandra", "DynamoDB", "Neo4j", "pgvector",
    "AWS", "GCP", "Azure", "Kubernetes", "Docker", "Vercel", "Cloudflare",
    "Terraform", "GraphQL", "REST", "gRPC", "Kafka", "RabbitMQ", "Celery",
    "OpenAI", "Anthropic", "RAG", "LangChain", "PyTorch", "TensorFlow",
    "System Design", "Microservices", "Domain-Driven Design", "CI/CD",
    "Mentoring", "Team Leadership", "Communication",
}


def _extract_skills_from_text(text: str) -> list[str]:
    """Pick up known skill names case-insensitively, preserving canonical case."""
    lower = text.lower()
    hits: list[str] = []
    for skill in _KNOWN_SKILLS:
        if skill.lower() in lower and skill not in hits:
            hits.append(skill)
    return hits


# Capture lines that look like "Company — Role (2021–2023)" or
# "Role at Company, 2021–present".
_EXP_PATTERNS = [
    re.compile(
        r"^(?P<company>[A-Z][\w &.,'-]{1,60})\s*[—\-–]\s*(?P<role>[\w &.,'/-]{2,80})"
        r"\s*\((?P<start>\d{4})\s*[-–—]\s*(?P<end>\d{4}|present|current)\)",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?P<role>[\w &.,'/-]{2,80})\s+at\s+(?P<company>[A-Z][\w &.,'-]{1,60})"
        r"\s*,?\s*(?P<start>\d{4})\s*[-–—]\s*(?P<end>\d{4}|present|current)",
        re.IGNORECASE,
    ),
]


def _extract_experiences_from_text(text: str) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    experiences: list[dict[str, Any]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or len(stripped) > 200:
            continue
        for pattern in _EXP_PATTERNS:
            m = pattern.search(stripped)
            if not m:
                continue
            company = m.group("company").strip()
            role = m.group("role").strip()
            start = m.group("start")
            end_raw = m.group("end")
            key = (company.lower(), role.lower())
            if key in seen:
                continue
            seen.add(key)
            experiences.append(
                {
                    "company": company,
                    "role": role,
                    "location": None,
                    "employment_type": None,
                    "start_date": f"{start}-01-01" if start.isdigit() else None,
                    "end_date": (
                        f"{end_raw}-12-31"
                        if end_raw.isdigit()
                        else None
                    ),
                    "summary": None,
                    "skills": _extract_skills_from_text(stripped),
                    "achievements": [],
                }
            )
            break
    return experiences


# ----------------------- Phase F — output generation ---------------------


def _build_output_payload(user_prompt: str) -> dict[str, Any]:
    """Deterministic per-kind canned body so the OutputGenerationService
    pipeline (validate → cite → persist) is exercisable without network.
    """
    kind = _extract_kind(user_prompt)
    job_title = _extract_section(user_prompt, "Title:") or "the role"
    # persona = _extract_section(user_prompt, "Persona:") or "Default"  # currently unused; tone comes from system prompt
    target_role = _extract_section(user_prompt, "Target role:") or "the role"
    top_skills = _extract_csv_section(user_prompt, "## Top skills")
    top_experiences = _extract_bullet_section(user_prompt, "## Recent experiences")
    skill_phrase = ", ".join(top_skills[:3]) if top_skills else "the relevant stack"
    exp_phrase = top_experiences[0] if top_experiences else None

    if kind == "linkedin_message":
        body = (
            f"Hey — saw the {job_title} opening and it lines up with my "
            f"current focus on {skill_phrase}. "
            f"Happy to share a quick rundown of the closest project. "
            f"Open to a 15-minute chat this week?"
        )
        return {"title": None, "body_markdown": body}

    if kind == "recruiter_reply":
        body = (
            f"Thanks for reaching out about {job_title}. "
            f"I'm currently working on {skill_phrase}, and the scope looks "
            f"like a strong overlap. "
            f"What's the best next step — a quick intro call?"
        )
        return {"title": None, "body_markdown": body}

    if kind == "screening_answer":
        body = (
            f"I'm a strong fit because the role centres on {skill_phrase}, "
            f"which I've shipped end-to-end in prior work"
            + (f" ({exp_phrase})" if exp_phrase else "")
            + ".\n\n"
            "In the first 30 days I'd focus on a tight scoping pass, "
            "a baseline metrics dashboard, and one shipped slice of the "
            "highest-risk path."
        )
        return {"title": None, "body_markdown": body}

    if kind == "consulting_proposal":
        steps = "\n".join(
            [f"{i+1}. {step}" for i, step in enumerate(_consulting_steps(top_skills))]
        )
        body = (
            f"## Understanding\n"
            f"You're looking for {target_role.lower()} support on {job_title}. "
            f"The strongest leverage looks to be around {skill_phrase}.\n\n"
            f"## Proposed approach\n{steps}\n\n"
            f"## Why me\n"
            + (f"- {exp_phrase}\n" if exp_phrase else "")
            + f"- Hands-on with {skill_phrase}\n\n"
            f"## Engagement model\n"
            f"- 4-6 weeks, 20 hours/week\n"
            f"- Weekly written checkpoints\n\n"
            f"## Next steps\n"
            f"A 45-minute scoping call, then a fixed-scope written plan."
        )
        return {"title": f"Engagement proposal — {job_title}", "body_markdown": body}

    if kind == "resume_tailored":
        header = exp_phrase or "Recent role @ Company (2022–present)"
        bullets = "\n".join(
            [
                f"- Shipped {s} in production with measurable impact."
                for s in (top_skills[:4] or ["the relevant stack"])
            ]
        )
        body = f"### {header}\n{bullets}\n"
        return {"title": f"Tailored bullets — {job_title}", "body_markdown": body}

    if kind == "cover_letter":
        body = (
            f"Dear hiring team,\n\n"
            f"I'm writing about the {job_title} opening. "
            f"What caught my eye is the emphasis on {skill_phrase} — "
            f"that's been the focus of my recent work"
            + (f" ({exp_phrase})" if exp_phrase else "")
            + ".\n\n"
            f"In prior engagements I've shipped projects across "
            f"{skill_phrase}, with concrete responsibility for design "
            f"decisions and delivery. I'd bring the same hands-on cadence "
            f"to your team.\n\n"
            f"I'd welcome a brief conversation about the role. "
            f"Available most weekday afternoons."
        )
        return {"title": f"Cover letter — {job_title}", "body_markdown": body}

    # Default: Upwork-style proposal.
    body = (
        f"Hi — I'd like to put my name in for {job_title}. "
        f"The closest analogue in my work is "
        + (exp_phrase or "a recent project")
        + f", where I delivered against {skill_phrase}.\n\n"
        f"My approach would be a short discovery pass, then a tight first "
        f"slice within two weeks so we can validate scope on real output.\n\n"
        f"Happy to share the closest project and walk through the plan on a call."
    )
    return {"title": None, "body_markdown": body}


def _extract_kind(user_prompt: str) -> str:
    m = re.search(r"OUTPUT_GENERATION:\s*kind=([a-z_]+)", user_prompt)
    return m.group(1) if m else "upwork_proposal"


def _extract_section(user_prompt: str, label: str) -> str | None:
    for line in user_prompt.splitlines():
        if line.startswith(label):
            return line.split(":", 1)[-1].strip() or None
    return None


def _extract_csv_section(user_prompt: str, header: str) -> list[str]:
    lines = user_prompt.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(header):
            for follow in lines[i + 1 : i + 4]:
                if follow.strip() and not follow.startswith("#"):
                    return [s.strip() for s in follow.split(",") if s.strip()]
    return []


def _extract_bullet_section(user_prompt: str, header: str) -> list[str]:
    lines = user_prompt.splitlines()
    out: list[str] = []
    capturing = False
    for line in lines:
        if line.strip().startswith(header):
            capturing = True
            continue
        if capturing:
            if line.startswith("- "):
                out.append(line[2:].strip())
            elif line.startswith("#"):
                break
            elif not line.strip():
                # Allow a blank line between header and first bullet.
                if out:
                    break
    return out


def _consulting_steps(skills: list[str]) -> list[str]:
    if skills:
        head = skills[0]
        return [
            f"Discovery: 2-3 stakeholder interviews focused on {head}.",
            "Scoping doc with explicit success metrics + 3 risks.",
            f"First slice: smallest end-to-end working path through {head}.",
            "Iteration on real production data — weekly written checkpoint.",
            "Handoff + 2-week support window.",
        ]
    return [
        "Discovery: stakeholder interviews.",
        "Scoping doc with success metrics + risks.",
        "First slice: smallest end-to-end working path.",
        "Iteration on real production data.",
        "Handoff + 2-week support window.",
    ]
