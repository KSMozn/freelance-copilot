"""StudentCoachService — inline coaching for the student wizard.

The wizard surfaces gentle guidance at each step:
  * Email check (rule-based): flag funky personal addresses ("xx_cool_xx"),
    excessive numbers, common nickname patterns, free providers with
    suspicious local parts. Suggest a name-based fallback when we have a
    full name. NEVER block — only warn.
  * Photo check (LLM vision): pass the bytes to the AI provider and get a
    short verdict on whether the picture reads as professional (face
    centred, neutral background, decent lighting). Warnings only.
  * Text rewrite (LLM): take a summary / project blurb / volunteer
    description and return a tightened, action-oriented rewrite the
    student can accept or ignore.

Coaching never blocks. The DTO carries `warnings` + `suggestions`; the
wizard chooses how to surface them and the student always has final say.
"""
from __future__ import annotations

import json
import logging
import re

from app.application.dto.student_dto import (
    CoachSuggestion,
    CoachWarning,
    DraftSummaryResponse,
    EmailCoachRequest,
    EmailCoachResponse,
    PhotoCoachResponse,
    TextCoachRequest,
    TextCoachResponse,
)
from app.domain.providers.ai_provider import AIProvider
from app.infrastructure.db.models.student_profile import (
    StudentProfile,
    StudentProfileEntry,
)

logger = logging.getLogger(__name__)


# ---- email rules -------------------------------------------------------

# Free providers students often use — fine on their own, but a hint that
# the *local part* matters more.
_FREE_PROVIDERS = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "icloud.com",
    "live.com",
    "aol.com",
    "protonmail.com",
}

# Substrings that strongly read as a personal/funky address.
_FUNKY_TOKENS = (
    "cool",
    "sexy",
    "cute",
    "love",
    "babe",
    "gangsta",
    "killer",
    "ninja",
    "boss",
    "king",
    "queen",
    "princess",
    "savage",
    "swag",
    "lol",
    "xoxo",
    "hottie",
    "dragon",
    "wolf",
    "lord",
    "master",
    "thug",
)

_LEADING_OR_TRAILING_NUMBERS = re.compile(r"^\d+|\d+$")
_REPEATED_CHARS = re.compile(r"(.)\1{3,}")
_SEPARATOR_FLOOD = re.compile(r"[_.\-]{2,}")


def _slugify_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z]+", "", name).lower()
    return cleaned


def _build_suggested_addresses(full_name: str | None, domain: str) -> list[str]:
    if not full_name:
        return []
    parts = [p for p in re.split(r"\s+", full_name.strip()) if p]
    if not parts:
        return []
    first = _slugify_name(parts[0])
    last = _slugify_name(parts[-1]) if len(parts) > 1 else ""
    out: list[str] = []
    if first and last:
        out.append(f"{first}.{last}@{domain}")
        out.append(f"{first}{last}@{domain}")
        out.append(f"{first[0]}{last}@{domain}")
    elif first:
        out.append(f"{first}@{domain}")
    # Deduplicate while preserving order.
    seen: set[str] = set()
    return [a for a in out if not (a in seen or seen.add(a))]


def check_email(req: EmailCoachRequest) -> EmailCoachResponse:
    raw = req.email.strip()
    warnings: list[CoachWarning] = []
    suggestions: list[CoachSuggestion] = []

    if "@" not in raw or raw.count("@") != 1:
        warnings.append(
            CoachWarning(
                code="email_malformed",
                message="That doesn't look like a valid email address.",
                severity="block",
            )
        )
        return EmailCoachResponse(ok=False, warnings=warnings)

    local, domain = raw.split("@", 1)
    local_lc = local.lower()
    domain_lc = domain.lower()

    if any(token in local_lc for token in _FUNKY_TOKENS):
        warnings.append(
            CoachWarning(
                code="email_unprofessional_word",
                message=(
                    "Recruiters skim email addresses fast. Words like this "
                    "can read as casual — consider a name-based address."
                ),
            )
        )

    digits = sum(c.isdigit() for c in local_lc)
    if digits >= 4:
        warnings.append(
            CoachWarning(
                code="email_too_many_digits",
                message=(
                    "Lots of digits can make addresses look generated. A "
                    "firstname.lastname@ address is usually safer."
                ),
            )
        )

    if _LEADING_OR_TRAILING_NUMBERS.search(local_lc) and digits >= 2:
        warnings.append(
            CoachWarning(
                code="email_year_or_birthdate",
                message=(
                    "Numbers at the start/end (often a birth year) can age "
                    "you on a CV. Consider dropping them."
                ),
            )
        )

    if _REPEATED_CHARS.search(local_lc):
        warnings.append(
            CoachWarning(
                code="email_repeated_chars",
                message="Repeated characters (xxxxx) read as informal.",
            )
        )

    if _SEPARATOR_FLOOD.search(local_lc):
        warnings.append(
            CoachWarning(
                code="email_separator_flood",
                message="Too many dots / dashes / underscores in a row.",
            )
        )

    if "@" in raw and domain_lc in _FREE_PROVIDERS and len(local_lc) < 4:
        warnings.append(
            CoachWarning(
                code="email_too_short_local",
                message=(
                    "Very short prefixes (1-3 chars) can look like a "
                    "throwaway. Use your full name where possible."
                ),
                severity="info",
            )
        )

    # If the student insists, we still accept — the wizard sends
    # `confirm=true` to suppress these next time round.
    if warnings and req.full_name:
        for addr in _build_suggested_addresses(req.full_name, domain):
            suggestions.append(
                CoachSuggestion(
                    label=addr,
                    value=addr,
                    rationale="Name-based addresses read as professional.",
                )
            )

    return EmailCoachResponse(
        ok=not any(w.severity == "block" for w in warnings),
        warnings=warnings,
        suggestions=suggestions,
    )


# ---- photo check (LLM vision) -----------------------------------------


_PHOTO_SYSTEM_PROMPT = (
    "You are a CV photo reviewer. The user has uploaded a profile picture "
    "to put on their CV. Judge whether it would read as professional to a "
    "recruiter. Be supportive — flag specific issues but do not gatekeep.\n\n"
    "Return strict JSON:\n"
    "{\n"
    '  "is_professional": boolean,\n'
    '  "summary": "one short sentence",\n'
    '  "issues": ["short bullet", ...]\n'
    "}\n\n"
    "Issues to consider: face clearly visible, neutral background, decent "
    "lighting, no sunglasses, dressed presentably, single subject, not a "
    "selfie at an odd angle, not a cropped group photo, not a meme/filter."
)

_PHOTO_USER_PROMPT = (
    "Review this CV photo. Return the JSON object only."
)


def _summarise_for_prompt(
    profile: StudentProfile | None,
    entries: list[StudentProfileEntry],
) -> str:
    """Render the student's collected info as a compact text block the LLM
    can read. Skips empty fields so the prompt stays focused on what the
    student actually shared.
    """
    lines: list[str] = []
    if profile:
        if profile.full_name:
            lines.append(f"Name: {profile.full_name}")
        edu_bits = []
        if profile.degree:
            edu_bits.append(profile.degree)
        if profile.major:
            edu_bits.append(f"in {profile.major}")
        if profile.college:
            edu_bits.append(f"at {profile.college}")
        if profile.department:
            edu_bits.append(f"({profile.department})")
        if profile.graduation_year:
            edu_bits.append(f"(expected {profile.graduation_year})")
        if edu_bits:
            lines.append("Education: " + " ".join(edu_bits))
        if profile.gpa is not None:
            lines.append(f"GPA: {profile.gpa}")
        if profile.location:
            lines.append(f"Location: {profile.location}")

    by_kind: dict[str, list[StudentProfileEntry]] = {}
    for e in entries:
        by_kind.setdefault(e.kind, []).append(e)

    def fmt_skill(e: StudentProfileEntry) -> str:
        cat = (e.details or {}).get("category")
        return f"{e.title} ({cat})" if cat else e.title

    def fmt_project(e: StudentProfileEntry) -> str:
        stack = (e.details or {}).get("tech_stack")
        parts = [e.title]
        if e.description:
            parts.append(f"— {e.description}")
        if isinstance(stack, list) and stack:
            parts.append(f"[stack: {', '.join(map(str, stack))}]")
        return " ".join(parts)

    def fmt_simple(e: StudentProfileEntry) -> str:
        out = e.title
        if e.organization:
            out += f" @ {e.organization}"
        if e.description:
            out += f" — {e.description}"
        return out

    if by_kind.get("skill"):
        lines.append(
            "Skills: " + "; ".join(fmt_skill(e) for e in by_kind["skill"])
        )
    if by_kind.get("course"):
        lines.append(
            "Coursework: " + "; ".join(e.title for e in by_kind["course"])
        )
    if by_kind.get("project"):
        lines.append("Projects:")
        for e in by_kind["project"]:
            lines.append(f"  - {fmt_project(e)}")
    if by_kind.get("volunteer"):
        lines.append("Volunteer:")
        for e in by_kind["volunteer"]:
            lines.append(f"  - {fmt_simple(e)}")
    if by_kind.get("certificate"):
        lines.append(
            "Certificates: " + "; ".join(fmt_simple(e) for e in by_kind["certificate"])
        )
    if by_kind.get("language"):
        bits = []
        for e in by_kind["language"]:
            prof = (e.details or {}).get("proficiency")
            bits.append(f"{e.title} ({prof})" if prof else e.title)
        lines.append("Languages: " + ", ".join(bits))
    if by_kind.get("award"):
        lines.append(
            "Awards: " + "; ".join(fmt_simple(e) for e in by_kind["award"])
        )
    if by_kind.get("extracurricular"):
        lines.append(
            "Activities: "
            + "; ".join(fmt_simple(e) for e in by_kind["extracurricular"])
        )
    return "\n".join(lines)


class StudentCoachService:
    def __init__(self, ai_provider: AIProvider) -> None:
        self._ai = ai_provider

    # Email check is pure-rules and doesn't need a service instance, but
    # we expose it here so callers (FastAPI deps) get one service surface.
    @staticmethod
    def check_email(req: EmailCoachRequest) -> EmailCoachResponse:
        return check_email(req)

    async def check_photo(
        self, *, image_bytes: bytes, mime_type: str
    ) -> PhotoCoachResponse:
        try:
            raw = await self._ai.complete_json_with_image(
                system_prompt=_PHOTO_SYSTEM_PROMPT,
                user_prompt=_PHOTO_USER_PROMPT,
                image_bytes=image_bytes,
                image_mime_type=mime_type,
            )
        except Exception as exc:  # coach is best-effort; never gate the wizard
            logger.warning("Photo coach failed: %s", exc)
            return PhotoCoachResponse(
                ok=True,
                warnings=[
                    CoachWarning(
                        code="photo_check_unavailable",
                        message=(
                            "We couldn't review the photo right now. You can "
                            "still keep it — review later."
                        ),
                        severity="info",
                    )
                ],
            )
        data = raw.data or {}
        is_pro = bool(data.get("is_professional", True))
        summary = data.get("summary")
        issues = data.get("issues") or []
        warnings = [
            CoachWarning(
                code="photo_issue",
                message=str(i),
                severity="warn" if not is_pro else "info",
            )
            for i in issues
            if isinstance(i, str) and i.strip()
        ]
        return PhotoCoachResponse(
            ok=is_pro,
            summary=str(summary) if isinstance(summary, str) else None,
            warnings=warnings,
        )

    async def draft_summary(
        self,
        *,
        profile: StudentProfile | None,
        entries: list[StudentProfileEntry],
    ) -> DraftSummaryResponse:
        """Draft a CV headline + summary from what we know about the student.

        Called from the wizard's Summary step *after* basics, education,
        skills, courses, projects, etc. are filled in. A first-time
        student staring at an empty textarea usually freezes — this gives
        them a concrete starting point they can keep, edit, or scrap.
        """
        context = _summarise_for_prompt(profile, entries)
        if not context.strip():
            return DraftSummaryResponse(
                ok=False,
                headline="",
                summary="",
                notes=[
                    "Add a few details (education, skills, a project) and "
                    "we'll draft a summary for you."
                ],
            )

        system = (
            "You draft short, honest CV summaries for university / college "
            "students applying for internships and early-career roles. "
            "Constraints:\n"
            " - Use ONLY the facts the student gave. Never invent dates, "
            "   employers, projects, GPAs, or technologies.\n"
            " - Voice: first person, plain language, no buzzwords ('synergy',"
            " 'passionate', 'detail-oriented'). Sound like a thoughtful peer.\n"
            " - Headline: a single line, max ~80 chars. Lead with their "
            "role/year + 1-2 strongest interest areas.\n"
            " - Summary: 2-3 sentences, max ~60 words. Lead with who they "
            "are studying. Mention 1-2 concrete things they've built or "
            "studied. End with the kind of role they're looking for.\n\n"
            "Return strict JSON: "
            '{"headline": "...", "summary": "...", "notes": ["..."]}'
        )
        user = (
            "Student profile:\n"
            f"{context}\n\n"
            "Draft headline + summary. Return JSON only."
        )
        try:
            raw = await self._ai.complete_json(
                system_prompt=system, user_prompt=user
            )
        except Exception as exc:  # coach is best-effort; never gate the wizard
            logger.warning("Draft summary failed: %s", exc)
            return DraftSummaryResponse(
                ok=False,
                headline="",
                summary="",
                notes=["AI unavailable — write a draft yourself for now."],
            )
        data = raw.data or {}
        headline = data.get("headline")
        summary = data.get("summary")
        if not isinstance(headline, str) or not isinstance(summary, str):
            return DraftSummaryResponse(
                ok=False,
                headline="",
                summary="",
                notes=["Couldn't parse the draft. Try regenerating."],
            )
        notes_raw = data.get("notes") or []
        notes = [str(n) for n in notes_raw if isinstance(n, str)]
        return DraftSummaryResponse(
            ok=True,
            headline=headline.strip(),
            summary=summary.strip(),
            notes=notes,
        )

    async def improve_text(self, req: TextCoachRequest) -> TextCoachResponse:
        system = (
            "You help students sharpen short CV blurbs. The student writes "
            "in their own voice; you preserve it. Tighten verbs, add "
            "concrete outcomes only when the student already implied them, "
            "and stay truthful — never invent achievements or numbers. "
            "Keep length within ~15% of the original.\n\n"
            "Return strict JSON: "
            '{"rewritten": "...", "notes": ["...", ...]}'
        )
        context_blob = json.dumps(req.context or {}, ensure_ascii=False)
        user = (
            f"Field: {req.field}\n"
            f"Context (may be empty): {context_blob}\n"
            f"Original:\n{req.text}\n\n"
            "Rewrite. Return JSON only."
        )
        try:
            raw = await self._ai.complete_json(
                system_prompt=system, user_prompt=user
            )
        except Exception as exc:  # coach is best-effort; never gate the wizard
            logger.warning("Text coach failed: %s", exc)
            return TextCoachResponse(
                ok=False, rewritten=req.text, notes=["AI unavailable"]
            )
        data = raw.data or {}
        rewritten = data.get("rewritten")
        if not isinstance(rewritten, str) or not rewritten.strip():
            return TextCoachResponse(
                ok=False, rewritten=req.text, notes=["No rewrite returned"]
            )
        notes_raw = data.get("notes") or []
        notes = [str(n) for n in notes_raw if isinstance(n, str)]
        return TextCoachResponse(ok=True, rewritten=rewritten, notes=notes)
