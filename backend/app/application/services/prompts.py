"""Prompt templates for the job analyzer.

Bumping `PROMPT_VERSION` invalidates downstream caches / scoring traceability —
older analyses keep their original `prompt_version` recorded.
"""

PROMPT_VERSION = "analyzer-v2"

SYSTEM_PROMPT = """You are a senior software-consulting analyst who screens Upwork \
jobs for a freelance engineer.

Your job: extract structured information from a pasted job post so a downstream \
scoring engine can decide whether the freelancer should apply.

Rules:
- Reply with a single JSON object that conforms exactly to the schema described \
  by the user message. Output nothing else — no prose, no markdown, no code fences.
- All fields are required keys. Use null only where the schema permits.
- Use the exact lowercase enum values: complexity ∈ {low, medium, high}; \
  risk_level ∈ {low, medium, high}; severity ∈ {low, medium, high}; \
  budget_assessment ∈ {low, reasonable, high, unclear}; \
  seniority_level ∈ {junior, mid, senior, lead, staff, principal}.
- `summary` is 2–3 sentences in plain English.
- Skill names are short canonical forms (e.g. "Python", "FastAPI", "PostgreSQL").
- If the post is light on detail, infer reasonable defaults and reflect that \
  uncertainty in `budget_assessment` and the risks list — do not fabricate facts.
- `stack_requirements`: a categorized list of every distinct stack item the \
  post asks for. Each item has `category` (one of: tech_stack, architecture, \
  cloud_platform, ai_llm, authentication, billing, integrations, database, \
  devops, testing, deployment, security, nice_to_have), `name` (short canonical \
  form), and `importance` 1–5 (5 = "core / must-have"; 1 = "barely mentioned"). \
  Cover every item you'd want to call out in a proposal — typically 5–15 items.
"""

USER_PROMPT_TEMPLATE = """Analyze the following Upwork job post and return JSON \
matching this schema (TypeScript-style notation, all keys required):

{{
  "summary": string,
  "required_skills": string[],
  "preferred_skills": string[],
  "technologies": string[],
  "business_domain": string | null,
  "seniority_level": "junior" | "mid" | "senior" | "lead" | "staff" | "principal" | null,
  "complexity": "low" | "medium" | "high",
  "estimated_hours_min": number | null,
  "estimated_hours_max": number | null,
  "budget_assessment": "low" | "reasonable" | "high" | "unclear",
  "client_intent": string | null,
  "hidden_requirements": string[],
  "deliverables": string[],
  "risks": {{ "risk": string, "severity": "low"|"medium"|"high", "mitigation": string }}[],
  "red_flags": string[],
  "green_flags": string[],
  "questions_to_ask_client": string[],
  "risk_level": "low" | "medium" | "high",
  "communication_required": string | null,
  "stack_requirements": {{
    "category": "tech_stack" | "architecture" | "cloud_platform" | "ai_llm"
              | "authentication" | "billing" | "integrations" | "database"
              | "devops" | "testing" | "deployment" | "security" | "nice_to_have",
    "name": string,
    "importance": 1 | 2 | 3 | 4 | 5
  }}[]
}}

--- JOB METADATA ---
Title: {title}
Budget: {budget}
Proposals so far: {proposal_count}

--- JOB DESCRIPTION ---
{description}
--- END ---

Return JSON only.
"""


def build_user_prompt(
    *,
    title: str,
    description: str,
    budget: str,
    proposal_count: int | str,
) -> str:
    return USER_PROMPT_TEMPLATE.format(
        title=title,
        description=description,
        budget=budget,
        proposal_count=proposal_count,
    )
