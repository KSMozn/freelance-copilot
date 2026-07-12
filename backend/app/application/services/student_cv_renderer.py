"""StudentCvRenderer — Jinja2 + WeasyPrint CV builder.

Reads the student's `StudentProfile` + grouped `StudentProfileEntry`s,
renders an HTML CV through a Jinja2 template, and (for the PDF path) pipes
it into WeasyPrint. The HTML path drives the wizard's "Preview" step; the
PDF path drives the "Download" button.

The renderer treats every input as optional — if the student is on step 3
of the wizard with only Basics + Education filled, they still get a valid
(partial) CV. The template skips sections whose item list is empty.

WeasyPrint is a soft dependency: importing it fails if the system Pango /
Cairo / GDK libraries aren't installed (most often in a slim Linux base
image). When that happens we raise `WeasyPrintUnavailable` and the
endpoint returns 503 with a friendly hint, rather than crashing.
"""
from __future__ import annotations

import base64
import logging
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.application.url_policy import safe_external_http_url
from app.infrastructure.db.models.student_profile import (
    StudentProfile,
    StudentProfileEntry,
)

logger = logging.getLogger(__name__)


class WeasyPrintUnavailable(RuntimeError):
    """Raised when WeasyPrint can't be imported (system libs missing).

    The HTTP layer maps this to 503 + a hint pointing at the Dockerfile
    note. The HTML preview path still works without WeasyPrint.
    """


_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "student_cv"

# Filesystem registry of bundled CV templates. The slug is the source
# of truth on both API and DB sides — a row in `cv_templates` whose
# slug isn't in this map is unreachable at render time (the resolver
# treats it as if it didn't exist). Adding a new template = ship the
# `.html` file + add a row here + add a seed row in a migration.
_TEMPLATE_REGISTRY: dict[str, str] = {
    "classic": "classic.html",
    "modern": "modern.html",
    "minimal": "minimal.html",
    "academic": "academic.html",
    "creative": "creative.html",
}
_DEFAULT_SLUG = "classic"

_EXTERNAL_LINK_RE = re.compile(r'<a href="(https?://[^"]+)"')


def _load_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


# Order in which sections render on the CV. Kinds the student hasn't
# added are silently skipped.
_SECTION_ORDER: tuple[tuple[str, str], ...] = (
    ("skill", "Skills"),
    ("language", "Languages"),
    ("project", "Projects"),
    ("internship", "Internships"),
    ("course", "Relevant Coursework"),
    ("certificate", "Certificates"),
    ("volunteer", "Volunteer Experience"),
    ("award", "Awards"),
    ("extracurricular", "Extracurriculars"),
)


def _photo_data_uri(photo_bytes: bytes | None, mime: str | None) -> str | None:
    """Inline the student's photo into the HTML as a base64 data URI.

    Bytes are passed in (pre-fetched from the BlobStore) rather than
    read here, because the photo may live in GCS — the renderer has no
    storage-backend awareness.
    """
    if not photo_bytes:
        return None
    mime = mime or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(photo_bytes).decode('ascii')}"


def _entry_to_view(entry: StudentProfileEntry) -> dict[str, Any]:
    view: dict[str, Any] = {
        "id": str(entry.id),
        "title": entry.title,
        "organization": entry.organization,
        "start_date": entry.start_date.isoformat() if entry.start_date else None,
        "end_date": entry.end_date.isoformat() if entry.end_date else None,
        "is_current": entry.is_current,
        "description": entry.description,
        "url": safe_external_http_url(entry.url),
        "details": dict(entry.details or {}),
    }
    if entry.kind == "project":
        # Compose a student-friendly paragraph from the structured
        # project fields. Falls back to the raw description when no
        # structured data is present (legacy rows created before the
        # richer form landed).
        view["narrative"] = _build_project_narrative(entry)
    elif entry.kind == "internship":
        # Internships render as a short summary + 2-4 bullets. Prefer
        # the LLM output persisted in `details.ai_bullets`; fall back to
        # a deterministic composer from responsibilities/achievements
        # so students who never clicked "Improve with AI" still get
        # something usable on their CV.
        details = view["details"]
        ai_summary = (details.get("ai_summary") or "").strip()
        ai_bullets = [
            str(b).strip()
            for b in (details.get("ai_bullets") or [])
            if isinstance(b, str) and b.strip()
        ]
        if ai_bullets:
            view["summary"] = ai_summary or None
            view["bullets"] = ai_bullets[:6]
        else:
            view["summary"] = None
            view["bullets"] = _deterministic_internship_bullets(entry)
    return view


# --- Internship deterministic fallback -----------------------------------
#
# Used when a student saved an internship without asking the coach to
# polish it. Emits up to 4 bullets from responsibilities/achievements/
# tools/skills using an action-verb rewrite lookup. Never invents.


_INTERNSHIP_ACTION_STARTER = "Contributed to"  # used when raw input lacks a verb


def _split_bullet_lines(raw: str | None) -> list[str]:
    """Split multi-line student input into candidate bullet lines.
    Preserves order, drops empties, trims markdown bullets ("- ", "* ")."""
    if not raw:
        return []
    out: list[str] = []
    for line in raw.splitlines():
        cleaned = line.strip().lstrip("*•-–— \t").strip()
        if not cleaned:
            continue
        out.append(cleaned)
    return out


_ACTION_VERB_PREFIXES: tuple[str, ...] = (
    "assisted",
    "built",
    "tested",
    "analyzed",
    "supported",
    "coordinated",
    "documented",
    "designed",
    "prepared",
    "presented",
    "reviewed",
    "developed",
    "created",
    "conducted",
    "collaborated",
    "researched",
    "improved",
    "delivered",
    "led",
)


def _polish_internship_line(line: str) -> str:
    """Tighten a raw student-typed line into a bullet-shaped sentence.
    Strips first-person ("I ", "I've "), leading weak verbs ("helped
    with", "was responsible for"), and adds a period. Cheap, no LLM."""
    text = line.strip()
    lower = text.lower()
    # First-person → drop
    for prefix in ("i've ", "i have ", "i was ", "i am ", "i ", "we "):
        if lower.startswith(prefix):
            text = text[len(prefix):].strip()
            lower = text.lower()
            break
    # Weak phrasing → replace
    weak_map = (
        ("was responsible for ", "Managed "),
        ("responsible for ", "Managed "),
        ("helped with ", "Supported "),
        ("helped to ", "Supported "),
        ("helped ", "Supported "),
        ("learned about ", "Studied "),
        ("learned ", "Studied "),
        ("worked on ", "Contributed to "),
    )
    for weak, strong in weak_map:
        if lower.startswith(weak):
            text = strong + text[len(weak):]
            lower = text.lower()
            break
    # Uppercase first letter
    if text:
        text = text[0].upper() + text[1:]
    # Ensure the sentence starts with an action verb — if not, prepend
    # a neutral one so the bullet still reads as a bullet.
    first_word = text.split(" ", 1)[0].rstrip(",.:;").lower() if text else ""
    if first_word and not any(
        first_word.startswith(v) for v in _ACTION_VERB_PREFIXES
    ):
        text = f"{_INTERNSHIP_ACTION_STARTER} {text[0].lower() + text[1:]}"
    if text and not text.endswith((".", "!", "?")):
        text = text + "."
    return text


def _deterministic_internship_bullets(
    entry: StudentProfileEntry,
) -> list[str]:
    details = dict(entry.details or {})
    bullets: list[str] = []

    for line in _split_bullet_lines(details.get("responsibilities")):
        bullets.append(_polish_internship_line(line))
        if len(bullets) >= 4:
            return bullets

    for line in _split_bullet_lines(details.get("achievements")):
        bullets.append(_polish_internship_line(line))
        if len(bullets) >= 4:
            return bullets

    tools = [str(t).strip() for t in (details.get("tools") or []) if str(t).strip()]
    if tools and len(bullets) < 4:
        bullets.append(
            f"Used {_english_join(tools[:5])} while contributing to the team's work."
        )

    skills = [
        str(s).strip()
        for s in (details.get("skills_gained") or [])
        if str(s).strip()
    ]
    if skills and len(bullets) < 4:
        bullets.append(
            f"Developed skills in {_english_join(skills[:5])} through hands-on tasks."
        )

    if not bullets and (entry.description or "").strip():
        bullets.append(_polish_internship_line(entry.description.strip()))

    return bullets[:4]


# --- Project narrative --------------------------------------------------
#
# Given a project entry's structured details (roles, tech, features,
# hardest_part) plus its plain-text description, compose a short
# paragraph suitable for a student CV. The composition rules are strict
# so the output never invents content:
#
#   * Every clause comes from data the student actually provided.
#   * Empty fields are skipped — no placeholder text.
#   * Roles and tech are formatted as natural English (Oxford comma,
#     "and" before the last item).
#
# Callers should treat the return value as the primary description text
# for the project. Templates fall back to `item.description` when
# `item.narrative` is None (legacy row with no structured details).


_WORK_ROLE_LABELS: dict[str, str] = {
    "frontend": "frontend",
    "backend": "backend",
    "database": "database",
    "ui_design": "UI design",
    "testing": "testing",
}


def _english_join(items: list[str]) -> str:
    cleaned = [i for i in items if i]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return ", ".join(cleaned[:-1]) + f", and {cleaned[-1]}"


def _project_role_phrase(roles: list[str]) -> str | None:
    if not roles:
        return None
    work_areas = [
        _WORK_ROLE_LABELS[key]
        for key in ("frontend", "backend", "database", "ui_design", "testing")
        if key in roles
    ]
    team = "team" in roles
    solo = "solo" in roles and not team  # "team" wins if both are set
    if work_areas:
        base = f"Worked on {_english_join(work_areas)} development"
        if team:
            return base + " as part of a team"
        if solo:
            return base + " solo"
        return base
    # No work area — team/solo alone don't warrant a sentence.
    return None


def _build_project_narrative(entry: StudentProfileEntry) -> str | None:
    details = dict(entry.details or {})
    description = (entry.description or "").strip()

    def _str_list(key: str) -> list[str]:
        raw = details.get(key) or []
        if not isinstance(raw, list):
            return []
        return [str(x) for x in raw if isinstance(x, str) and x.strip()]

    roles = _str_list("roles")
    tech = _str_list("tech_stack")
    features = str(details.get("features") or "").strip()
    hardest = str(details.get("hardest_part") or "").strip()

    sentences: list[str] = []
    if description:
        sentences.append(description.rstrip(". "))
    if features:
        sentences.append(f"Key features: {features.rstrip('. ')}")

    role_phrase = _project_role_phrase(roles)
    tech_phrase = _english_join(tech)
    if role_phrase and tech_phrase:
        sentences.append(f"{role_phrase} using {tech_phrase}")
    elif role_phrase:
        sentences.append(role_phrase)
    elif tech_phrase:
        sentences.append(f"Built with {tech_phrase}")

    if hardest:
        sentences.append(f"The hardest part was {hardest.rstrip('. ')}")

    if not sentences:
        return None
    return ". ".join(sentences) + "."


class StudentCvRenderer:
    def __init__(self) -> None:
        self._env = _load_env()

    @staticmethod
    def list_template_slugs() -> set[str]:
        """Slugs of every filesystem-backed template.

        The DB-side registry (`cv_templates`) is expected to be a subset
        of these — anything outside is silently ignored by the resolver.
        """
        return set(_TEMPLATE_REGISTRY)

    def _resolve_template_file(self, slug: str | None) -> str:
        if slug and slug in _TEMPLATE_REGISTRY:
            return _TEMPLATE_REGISTRY[slug]
        return _TEMPLATE_REGISTRY[_DEFAULT_SLUG]

    def build_context(
        self,
        *,
        profile: StudentProfile | None,
        entries: list[StudentProfileEntry],
        photo_bytes: bytes | None = None,
        photo_mime: str | None = None,
    ) -> dict[str, Any]:
        # Group + sort entries per section.
        grouped: dict[str, list[StudentProfileEntry]] = {}
        for e in entries:
            grouped.setdefault(e.kind, []).append(e)
        for items in grouped.values():
            items.sort(
                key=lambda x: (
                    x.sort_order,
                    -(x.start_date.toordinal() if x.start_date else 0),
                )
            )

        sections = [
            {
                "kind": kind,
                "label": label,
                # `entries` (not `items`) — `dict.items` would shadow the
                # key in Jinja's attribute lookup.
                "entries": [_entry_to_view(e) for e in grouped.get(kind, [])],
            }
            for kind, label in _SECTION_ORDER
            if grouped.get(kind)
        ]

        return {
            "profile": {
                "full_name": (profile.full_name if profile else None) or "Your name",
                "professional_email": (
                    profile.professional_email if profile else None
                ),
                "phone": profile.phone if profile else None,
                "location": profile.location if profile else None,
                "date_of_birth": (
                    profile.date_of_birth.strftime("%d %B %Y")
                    if profile and profile.date_of_birth
                    else None
                ),
                "college": profile.college if profile else None,
                "department": profile.department if profile else None,
                "degree": profile.degree if profile else None,
                "major": profile.major if profile else None,
                "graduation_year": (
                    profile.graduation_year if profile else None
                ),
                "gpa": str(profile.gpa) if profile and profile.gpa is not None else None,
                "summary": profile.summary if profile else None,
                "headline": profile.headline if profile else None,
                "links": {
                    key: url
                    for key, value in (profile.links or {}).items()
                    if (url := safe_external_http_url(value)) is not None
                }
                if profile
                else {},
                "interests": list(profile.interests or []) if profile else [],
                # Crop transform — matches what the student set in the
                # wizard. Defaults land at "centered, fitted" so the
                # empty-profile preview render still looks right.
                "photo_offset_x": profile.photo_offset_x if profile else 50,
                "photo_offset_y": profile.photo_offset_y if profile else 50,
                "photo_zoom": profile.photo_zoom if profile else 100,
            },
            "photo_data_uri": _photo_data_uri(photo_bytes, photo_mime),
            "sections": sections,
        }

    def render_html(
        self,
        *,
        profile: StudentProfile | None,
        entries: list[StudentProfileEntry],
        photo_bytes: bytes | None = None,
        photo_mime: str | None = None,
        template_slug: str | None = None,
    ) -> str:
        ctx = self.build_context(
            profile=profile,
            entries=entries,
            photo_bytes=photo_bytes,
            photo_mime=photo_mime,
        )
        template = self._env.get_template(self._resolve_template_file(template_slug))
        html = template.render(**ctx)
        return _EXTERNAL_LINK_RE.sub(
            r'<a target="_blank" rel="noopener" href="\1"',
            html,
        )

    def render_pdf(
        self,
        *,
        profile: StudentProfile | None,
        entries: list[StudentProfileEntry],
        photo_bytes: bytes | None = None,
        photo_mime: str | None = None,
        template_slug: str | None = None,
    ) -> bytes:
        html = self.render_html(
            profile=profile,
            entries=entries,
            photo_bytes=photo_bytes,
            photo_mime=photo_mime,
            template_slug=template_slug,
        )
        try:
            from weasyprint import HTML  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover — environment-dependent
            raise WeasyPrintUnavailable(
                "WeasyPrint isn't installed. Install system deps (cairo, "
                "pango, gdk-pixbuf, libffi) and `weasyprint` Python package."
            ) from exc
        except OSError as exc:  # pragma: no cover — environment-dependent
            # WeasyPrint raises OSError when the underlying GObject libs
            # are missing (typical on a fresh slim image).
            raise WeasyPrintUnavailable(
                "WeasyPrint's native libraries (cairo / pango / gdk-pixbuf) "
                "aren't available. Update your Dockerfile to install them."
            ) from exc
        return HTML(string=html).write_pdf() or b""
