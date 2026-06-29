"""Prompts for the screenshot → job-import flow.

The model receives the system prompt + a text user prompt + the screenshot
as an image content block. It must respond with a single JSON object that
matches `JobImportSchema`.
"""

PROMPT_VERSION = "job-import-v1"

SYSTEM_PROMPT = """You are extracting structured fields from a screenshot of \
a freelance job post (Upwork-style).

Rules:
- Respond with a single JSON object that matches the user prompt's schema. \
  No prose, no markdown, no code fences.
- All fields are optional except `title` and `description`. If a field is not \
  visible in the screenshot, omit it (do NOT invent values).
- Preserve numbers, currency symbols, and exact phrasing where possible.
- For hourly rates expressed as a range (e.g. "$25.00–$47.00 hourly"), set \
  `budget_type` to "hourly", `budget_min` to the lower number, and \
  `budget_max` to the higher number. For fixed-price posts, use "fixed".
- Skills lists: only include items actually shown in the screenshot. Keep \
  the platform's casing (e.g. ".NET Framework", "HTML5", "JavaScript").
- Pre-application questions: capture the full question text, no numbering.
- Never include personally identifying client info beyond what the post shows \
  (no addresses, phone numbers, emails).

If the screenshot is clearly NOT a job post (random photo, blurry, blank), \
return a JSON object with empty title + description so the caller can fail \
the import cleanly.
"""

USER_PROMPT = """Extract the job-post fields from the attached screenshot. \
Return JSON only with this schema (TypeScript notation, all keys allowed):

{
  "title": string,                    // required
  "description": string,              // required — the post's summary / body text
  "source_url": string | null,        // the Upwork job URL if visible
  "budget_type": "fixed" | "hourly" | null,
  "budget_min": number | null,
  "budget_max": number | null,
  "currency": string,                 // 3-letter, default "USD"
  "proposal_count": number | null,
  "project_duration": string | null,  // e.g. "1 to 3 months"
  "project_type": string | null,      // e.g. "Ongoing project"
  "experience_level": string | null,  // e.g. "Expert" / "Intermediate" / "Entry"
  "location": string | null,          // e.g. "Worldwide" / "United States only"
  "posted_at": string | null,         // verbatim, e.g. "1 hour ago"
  "mandatory_skills": string[],
  "nice_to_have_skills": string[],
  "questions": string[]               // pre-application questions
}

Return JSON only."""
