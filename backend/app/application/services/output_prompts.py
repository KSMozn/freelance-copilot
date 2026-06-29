"""Per-kind system prompts for the unified OutputGenerationService.

Each prompt asks the AI for a STRICT JSON object with the same shape:

    {
      "title": optional string,
      "body_markdown": string  # the artifact's full content, in markdown
    }

This lets the orchestrator stay kind-agnostic and the mock provider stays
small. Tone / strategic_priorities / persona target_role are interpolated
into the system prompt at call time so every kind respects the active
persona.
"""
from __future__ import annotations

# Shared marker so the mock provider can route on prompt content.
OUTPUT_MARKER = "OUTPUT_GENERATION"


SYSTEM_BASE = """\
You generate a single professional artifact for a job application.

Return STRICT JSON with exactly two keys:
  - "title": a short label (string or null) — only set when the artifact
    is a standalone document (cover letter, consulting proposal); for
    chat-style outputs (LinkedIn message, recruiter reply), leave null.
  - "body_markdown": the artifact's full content, in clean markdown.

Hard rules:
  - Use ONLY facts the user actually has — pull from the experiences,
    projects, repositories, and certificates section of the context.
    Never fabricate companies, roles, dates, or metrics.
  - Match the requested tone exactly. Match the requested target_role.
  - Stay under the per-kind word budget. Brevity wins.
  - Do NOT include headers like "Dear Hiring Manager," unless the kind
    requires it.
"""


# Per-kind extensions appended to SYSTEM_BASE.
_KIND_PROMPTS: dict[str, str] = {
    "upwork_proposal": """\
KIND: Upwork proposal.
WORD BUDGET: 120-180 words.
OPENING: lead with the most specific concrete proof of fit (one project
or repo). Skip generic intros.
STRUCTURE: 3-4 short paragraphs. Last paragraph: invite a brief call.
FORMATTING: plain prose; no bullet lists. No section headers.
""",
    "cover_letter": """\
KIND: Cover letter (formal application).
WORD BUDGET: 200-300 words.
STRUCTURE: 3 paragraphs — (1) why this role / company, with one
specific signal you've researched. (2) 2-3 strongest matches with named
projects or experiences. (3) close with what you'd bring + availability.
FORMATTING: prose; optional one bullet list of 3 highlights only if it
adds clarity.
""",
    "recruiter_reply": """\
KIND: Recruiter reply (email back to a sourcing recruiter).
WORD BUDGET: 60-100 words.
TONE OVERRIDE: warm, professional, brief. Use a contraction or two.
STRUCTURE: thank them; one line on current focus; one line on whether
this fits; ask for the next step.
FORMATTING: plain text, no headers, no markdown bold.
""",
    "linkedin_message": """\
KIND: LinkedIn DM (cold outreach OR inbound reply).
WORD BUDGET: 40-70 words.
TONE OVERRIDE: casual, hook-first.
STRUCTURE: one-sentence hook tied to a specific signal; one sentence
on relevant work; one sentence call to action.
FORMATTING: plain text, no markdown.
""",
    "consulting_proposal": """\
KIND: Consulting engagement proposal.
WORD BUDGET: 400-600 words.
STRUCTURE:
  ## Understanding
  ## Proposed approach (3-5 numbered steps)
  ## Why me (2-3 named projects/repos)
  ## Engagement model (rate band, duration, deliverables)
  ## Next steps
FORMATTING: markdown headers, numbered lists where appropriate.
""",
    "screening_answer": """\
KIND: Screening-question answer (e.g. "Why are you a good fit for this role?").
WORD BUDGET: 100-160 words.
STRUCTURE: direct answer first sentence; one supporting paragraph with
2 concrete proofs; close on what you'd ship in the first 30 days.
FORMATTING: plain prose. One inline bold phrase is OK; no headers.
""",
    "resume_tailored": """\
KIND: Tailored resume bullets for this role.
WORD BUDGET: 8-12 bullets total across 2-3 experiences.
STRUCTURE: under each experience header (`### Role @ Company (dates)`),
write 3-5 bullets emphasising the skills the job most needs. Lead each
bullet with a strong verb; quantify when the source data allows.
FORMATTING: markdown — `### header` lines + `- bullet` lines only.
""",
}


def system_prompt_for(
    kind: str,
    *,
    tone: str,
    target_role: str | None,
    strategic_priorities: list[str],
) -> str:
    """Compose the system prompt for ``kind`` with persona overlay."""
    base = SYSTEM_BASE
    kind_block = _KIND_PROMPTS.get(kind, "")
    persona_block = (
        f"\nPERSONA TONE: {tone or 'pragmatic'}.\n"
        f"PERSONA TARGET ROLE: {target_role or 'not specified'}.\n"
    )
    if strategic_priorities:
        persona_block += (
            "PERSONA STRATEGIC PRIORITIES (lean into these where the job permits): "
            + ", ".join(strategic_priorities[:6])
            + ".\n"
        )
    return f"{base}\n{kind_block}\n{persona_block}".strip()


def user_prompt_for(
    kind: str,
    *,
    job_title: str,
    job_description: str,
    persona_name: str,
    persona_target_role: str | None,
    top_skills: list[str],
    top_projects: list[str],
    top_experiences: list[str],
) -> str:
    """Compose the user prompt — job context + persona evidence summary."""
    parts: list[str] = [
        f"{OUTPUT_MARKER}: kind={kind}",
        "",
        "## Job",
        f"Title: {job_title}",
        f"Description (truncated):\n{(job_description or '')[:2500]}",
        "",
        "## Acting as",
        f"Persona: {persona_name}",
        f"Target role: {persona_target_role or 'n/a'}",
    ]
    if top_skills:
        parts.extend(["", "## Top skills (proficiency ≥4 in this user's pot)",
                      ", ".join(top_skills[:25])])
    if top_projects:
        parts.extend(["", "## Top projects (most relevant work)",
                      "\n".join(f"- {p}" for p in top_projects[:8])])
    if top_experiences:
        parts.extend(["", "## Recent experiences",
                      "\n".join(f"- {e}" for e in top_experiences[:6])])
    return "\n".join(parts)
