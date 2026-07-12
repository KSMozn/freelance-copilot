"""CareerPackService — LinkedIn + GitHub content for the post-CV page.

Generates or reviews LinkedIn / GitHub starter content using the
student's CV data. Persists everything into the `career_pack` JSONB
column on `student_profiles` so revisiting a card shows the last
result without re-spending an AI call.

Safety guarantees (baked into every LLM prompt):
  * Uses only facts the student actually shared. Never invents dates,
    employers, projects, GPAs, metrics, or technologies.
  * No account creation, no password prompts, no LinkedIn scraping.
  * GitHub reviews only touch the public API (`api.github.com`) with
    no auth.
"""
from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from typing import Any, TypeVar
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.application.dto.career_pack_dto import (
    CareerPackRead,
    CareerStatus,
    GitHubGenerated,
    GitHubProjectReadme,
    GitHubReview,
    LinkedInGenerated,
    LinkedInProjectSuggestion,
    LinkedInReview,
)
from app.application.services.student_coach_service import _summarise_for_prompt
from app.domain.providers.ai_provider import AIProvider, AIRawResponse
from app.infrastructure.ai.errors import AIProviderError
from app.infrastructure.db.models.student_profile import (
    StudentProfile,
    StudentProfileEntry,
)

logger = logging.getLogger(__name__)

# Response-shape type for the AI plumbing below (any career-pack DTO).
_ModelT = TypeVar("_ModelT", bound=BaseModel)


class CareerPackError(RuntimeError):
    """Raised when a generation / review pass fails end-to-end.

    Endpoint layer maps this to 502 Bad Gateway (AI upstream) or 400
    (bad user input) depending on the wrapped cause.
    """


# --- Prompt scaffolding --------------------------------------------------

_HONESTY_RULES = (
    "Constraints — read carefully:\n"
    " * Use ONLY facts the student shared. NEVER invent employers, dates, GPAs,\n"
    "   metrics, project features, or technologies they didn't list.\n"
    " * The student is a university/college student writing their FIRST online\n"
    "   presence for internship / student-training applications.\n"
    " * Tone: encouraging, plain-language, no jargon, no buzzwords\n"
    "   ('passionate', 'synergy', 'detail-oriented', 'rockstar'). Sound\n"
    "   like a thoughtful peer, not a corporate recruiter.\n"
    " * No emojis in headlines or About / bio sections.\n"
    " * If a field is missing in the CV, leave the corresponding output empty\n"
    "   rather than making something up.\n"
)


_LINKEDIN_GENERATE_SYSTEM = (
    "You are a career coach writing LinkedIn starter content for a "
    "university student's first profile. Return strict JSON matching "
    "this shape:\n"
    '{\n'
    '  "headline": "one-line role + interests, max 200 chars",\n'
    '  "about": "3-5 sentence About section, first person, internship-focused",\n'
    '  "education_entry": "one paragraph formatted for LinkedIn Education",\n'
    '  "project_entries": [{"name": "...", "description": "..."}],\n'
    '  "skills": ["beginner-friendly skill", ...],\n'
    '  "checklist": ["step-by-step setup action", ...]\n'
    "}\n\n"
    f"{_HONESTY_RULES}"
    " * Checklist should walk the student through creating the profile "
    "manually on LinkedIn — pick a personal email, upload a clear photo, "
    "paste the headline, etc. Keep each step to one short sentence.\n"
    " * Skills: 8-15 items, from the student's declared skills and coursework.\n"
    " * project_entries: one entry per project on the CV, at most 5.\n"
)


_LINKEDIN_REVIEW_SYSTEM = (
    "You are a career coach reviewing a student's LinkedIn profile against "
    "their CV. You are given the extracted text of the student's LinkedIn "
    "PDF export and their CV facts. Do a real side-by-side comparison and "
    "return strict JSON:\n"
    '{\n'
    '  "summary": "one-sentence overall assessment",\n'
    '  "current_headline_review": "what the current headline gets right / wrong",\n'
    '  "suggested_headline": "improved headline",\n'
    '  "current_about_review": "what the current About section gets right / wrong",\n'
    '  "suggested_about": "improved About section",\n'
    '  "missing_sections": ["section present in CV but missing on LinkedIn", ...],\n'
    '  "skills_to_add": ["skill from CV not visible on LinkedIn", ...],\n'
    '  "projects_to_improve": ["short suggestion referencing a CV project", ...],\n'
    '  "checklist": ["actionable manual change", ...]\n'
    "}\n\n"
    f"{_HONESTY_RULES}"
    " * The LinkedIn text is a PDF extract — layout may be lossy. Be lenient\n"
    "   about ordering / missing whitespace when you compare.\n"
    " * When the CV mentions something the LinkedIn text doesn't (a project,\n"
    "   a skill, an award), flag it under missing_sections / skills_to_add /\n"
    "   projects_to_improve as appropriate.\n"
    " * If the LinkedIn text doesn't contain a headline or About section at\n"
    "   all, say so in the review field and put the fresh version in the\n"
    "   suggested_* field.\n"
    " * Cite CV facts by name — 'add your Jobs Web Application project' —\n"
    "   never invent unlisted work.\n"
    " * Keep the tone encouraging.\n"
)


_GITHUB_GENERATE_SYSTEM = (
    "You are a career coach preparing a student's GitHub starter kit. "
    "Return strict JSON:\n"
    '{\n'
    '  "username_suggestions": ["firstname-lastname", ...],\n'
    '  "bio": "one-line bio, max 160 chars",\n'
    '  "profile_readme": "full Markdown for github.com/USER/USER/README.md",\n'
    '  "project_readmes": [{"project_title": "...", "filename": "README.md", "body": "full Markdown"}],\n'
    '  "checklist": ["setup step", ...]\n'
    "}\n\n"
    f"{_HONESTY_RULES}"
    " * Username suggestions: 4-6 professional variants (firstname-lastname, "
    "firstname-lastname-dev, firstname-cs, firstname-code, etc.), lowercase, "
    "no digits unless in the student's name.\n"
    " * profile_readme: use the Careero-standard shape — greeting, education, "
    "interests, skills, projects (with short descriptions), currently learning, "
    "contact note. Real Markdown, with '#', '##', and bullet lists.\n"
    " * One project_readme per CV project, at most 5. Include short "
    "description, technologies used, features (only if the student listed "
    "them), what I learned, how to run (only if enough info exists), and a "
    "'Screenshots' placeholder heading.\n"
    " * Checklist: one short sentence per step, in order.\n"
)


_GITHUB_REVIEW_SYSTEM = (
    "You are a career coach reviewing a student's public GitHub profile. "
    "You are given the student's CV, their public GitHub profile fields, "
    "and a list of their public repositories. Return strict JSON:\n"
    '{\n'
    '  "profile_summary": "one-sentence overall assessment",\n'
    '  "has_profile_readme": true or false or null,\n'
    '  "suggested_bio": "improved bio if the current one is weak, else null",\n'
    '  "suggested_profile_readme": "full Markdown or null if profile already has a good README",\n'
    '  "project_readme_suggestions": [{"project_title": "...", "filename": "README.md", "body": "..."}],\n'
    '  "repo_checklist": ["actionable improvement", ...],\n'
    '  "cv_projects_to_add": ["CV project title", ...]\n'
    "}\n\n"
    f"{_HONESTY_RULES}"
    " * project_readme_suggestions: only for repos that would benefit "
    "AND for CV projects that appear to be on GitHub. Skip untouched repos.\n"
    " * cv_projects_to_add: CV projects that don't appear as repos yet.\n"
    " * If the profile has no repos, say so and suggest starting with the "
    "CV projects.\n"
)


# --- URL / username helpers ---------------------------------------------

# Profile-URL validation for links.linkedin / links.github lives on the
# StudentLinks DTO (`_normalize_profile_url`). This module only needs the
# username regex — used to normalize the identifier for the GitHub review.
_GITHUB_USERNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9\-]{0,38})$")


def _normalize_github_identifier(identifier: str) -> str:
    """Return a bare username from either 'foo' or 'https://github.com/foo/'."""
    ident = identifier.strip()
    if ident.startswith("http://") or ident.startswith("https://"):
        path = urlparse(ident).path.strip("/")
        # Take only the first path segment — strip trailing slashes, repo names, etc.
        ident = path.split("/", 1)[0] if path else ""
    if not _GITHUB_USERNAME_RE.match(ident):
        raise CareerPackError(f"Invalid GitHub username: {identifier!r}")
    return ident


# --- The service --------------------------------------------------------


class CareerPackService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        ai_provider: AIProvider,
        github_http_timeout_s: float = 6.0,
    ) -> None:
        self._session = session
        self._ai = ai_provider
        self._gh_timeout = github_http_timeout_s
        # Populated after each provider call so the endpoint can log
        # token usage + estimated cost into usage_events.meta.
        self.last_usage: dict[str, int] | None = None
        self.last_model: str | None = None
        self.last_provider: str | None = None

    def _capture(self, raw: AIRawResponse) -> AIRawResponse:
        self.last_usage = raw.usage
        self.last_model = raw.model
        self.last_provider = raw.provider
        return raw

    # ---------- Read ----------

    def read(self, profile: StudentProfile | None) -> CareerPackRead:
        pack = dict((profile.career_pack or {}) if profile else {})
        links = dict((profile.links or {}) if profile else {})
        linkedin_url = links.get("linkedin") or None
        github_url = links.get("github") or None

        def _shape(cls: type[_ModelT], key: str) -> _ModelT | None:
            raw = pack.get(key)
            if not isinstance(raw, dict):
                return None
            try:
                return cls.model_validate(raw)
            except ValidationError:
                logger.warning("Discarding malformed %s in career_pack", key)
                return None

        return CareerPackRead(
            linkedin_url=linkedin_url,
            github_url=github_url,
            linkedin_status=_status(pack, "linkedin", url=linkedin_url),
            github_status=_status(pack, "github", url=github_url),
            linkedin_generated=_shape(LinkedInGenerated, "linkedin_generated"),
            linkedin_recommendations=_shape(LinkedInReview, "linkedin_recommendations"),
            github_generated=_shape(GitHubGenerated, "github_generated"),
            github_recommendations=_shape(GitHubReview, "github_recommendations"),
            github_username=pack.get("github_username") or None,
        )

    # ---------- LinkedIn ----------

    async def generate_linkedin(
        self,
        *,
        profile: StudentProfile,
        entries: list[StudentProfileEntry],
    ) -> LinkedInGenerated:
        context = _summarise_for_prompt(profile, entries).strip()
        if not context:
            raise CareerPackError(
                "Add a few CV details first (education, skills, a project) — "
                "then we can generate LinkedIn content."
            )
        result = await self._call_ai(
            system=_LINKEDIN_GENERATE_SYSTEM,
            user=_user_prompt_generate("LinkedIn", context),
            schema=LinkedInGenerated,
            fallback=self._fallback_linkedin_generated,
        )
        self._patch(profile, {"linkedin_generated": result.model_dump()})
        await self._session.commit()
        return result

    async def review_linkedin(
        self,
        *,
        profile: StudentProfile,
        entries: list[StudentProfileEntry],
        linkedin_url: str,
        profile_text: str,
    ) -> LinkedInReview:
        url = linkedin_url.strip()
        if "linkedin.com/" not in url.lower():
            raise CareerPackError(
                "That doesn't look like a LinkedIn profile URL."
            )
        context = _summarise_for_prompt(profile, entries).strip()
        if not context:
            raise CareerPackError(
                "Add a few CV details first (education, skills, a project) — "
                "then we can review your LinkedIn."
            )
        trimmed = profile_text.strip()[:15000]
        if len(trimmed) < 40:
            raise CareerPackError(
                "The uploaded LinkedIn export looks empty. Try re-exporting "
                "from LinkedIn → Me → Save to PDF."
            )
        result = await self._call_ai(
            system=_LINKEDIN_REVIEW_SYSTEM,
            user=(
                f"Student's LinkedIn profile URL: {url}\n\n"
                "Student's CV facts (source of truth — do not invent beyond these):\n"
                f"{context}\n\n"
                "Text extracted from the student's LinkedIn PDF export:\n"
                "---\n"
                f"{trimmed}\n"
                "---\n\n"
                "Compare the LinkedIn profile to the CV. Return JSON only."
            ),
            schema=LinkedInReview,
            fallback=self._fallback_linkedin_review,
        )
        self._patch(
            profile,
            {"linkedin_recommendations": result.model_dump()},
        )
        await self._session.commit()
        return result

    # ---------- GitHub ----------

    async def generate_github(
        self,
        *,
        profile: StudentProfile,
        entries: list[StudentProfileEntry],
    ) -> GitHubGenerated:
        context = _summarise_for_prompt(profile, entries).strip()
        if not context:
            raise CareerPackError(
                "Add a few CV details first (name, education, a project) — "
                "then we can generate GitHub content."
            )
        result = await self._call_ai(
            system=_GITHUB_GENERATE_SYSTEM,
            user=_user_prompt_generate("GitHub", context),
            schema=GitHubGenerated,
            fallback=self._fallback_github_generated,
        )
        self._patch(profile, {"github_generated": result.model_dump()})
        await self._session.commit()
        return result

    async def review_github(
        self,
        *,
        profile: StudentProfile,
        entries: list[StudentProfileEntry],
        identifier: str,
    ) -> GitHubReview:
        username = _normalize_github_identifier(identifier)
        gh_info = await self._fetch_github_public(username)
        context = _summarise_for_prompt(profile, entries).strip()
        result = await self._call_ai(
            system=_GITHUB_REVIEW_SYSTEM,
            user=(
                "Student's CV facts:\n"
                f"{context or '(empty)'}\n\n"
                f"GitHub profile (public API):\n{json.dumps(gh_info, indent=2)}\n\n"
                "Return JSON only."
            ),
            schema=GitHubReview,
            fallback=self._fallback_github_review,
        )
        self._patch(
            profile,
            {
                "github_recommendations": result.model_dump(),
                "github_username": username,
            },
        )
        await self._session.commit()
        return result

    # ---------- Clear ----------

    async def clear(
        self,
        *,
        profile: StudentProfile,
        side: str,
        kind: str,
    ) -> None:
        """Drop the generated content or the review recommendations for one
        side of the card. Leaves the URL and any other keys intact.
        """
        key = f"{side}_{'generated' if kind == 'generated' else 'recommendations'}"
        pack = dict(profile.career_pack or {})
        if key in pack:
            pack.pop(key)
            profile.career_pack = pack
            flag_modified(profile, "career_pack")
            await self._session.commit()

    # ---------- GitHub public API ----------

    async def _fetch_github_public(self, username: str) -> dict[str, Any]:
        """Fetch public profile + top repos. Never authenticated.

        We deliberately keep the surface tiny: bio, repo names + descriptions
        + primary languages. That's enough for the LLM to decide what needs
        a README or a description.
        """
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "Careero"}
        async with httpx.AsyncClient(timeout=self._gh_timeout, headers=headers) as client:
            try:
                user_resp = await client.get(f"https://api.github.com/users/{username}")
                if user_resp.status_code == 404:
                    raise CareerPackError(
                        f"No public GitHub account found for '{username}'."
                    )
                user_resp.raise_for_status()
                repos_resp = await client.get(
                    f"https://api.github.com/users/{username}/repos",
                    params={"per_page": 30, "sort": "updated"},
                )
                repos_resp.raise_for_status()
            except httpx.HTTPError as exc:
                logger.warning("GitHub public API failed for %s: %s", username, exc)
                raise CareerPackError(
                    "Couldn't reach GitHub right now. Try again in a moment."
                ) from exc
        user_data = user_resp.json()
        repos_data = repos_resp.json() or []
        return {
            "login": user_data.get("login"),
            "name": user_data.get("name"),
            "bio": user_data.get("bio"),
            "public_repos": user_data.get("public_repos"),
            "followers": user_data.get("followers"),
            "location": user_data.get("location"),
            "blog": user_data.get("blog"),
            "repos": [
                {
                    "name": r.get("name"),
                    "description": r.get("description"),
                    "language": r.get("language"),
                    "fork": r.get("fork"),
                    "archived": r.get("archived"),
                    "stargazers_count": r.get("stargazers_count"),
                    "topics": r.get("topics") or [],
                }
                for r in repos_data
                if not r.get("fork")  # keep signal high; skip forks
            ][:20],
        }

    # ---------- Persistence helper ----------

    def _patch(self, profile: StudentProfile, updates: dict[str, Any]) -> None:
        """Merge into career_pack and flag the JSONB column dirty.

        SQLAlchemy tracks assignment to `profile.career_pack`, but
        mutating the dict in place needs a `flag_modified` hint so the
        update is emitted on flush.
        """
        pack = dict(profile.career_pack or {})
        pack.update(updates)
        profile.career_pack = pack
        flag_modified(profile, "career_pack")

    # ---------- AI plumbing ----------

    async def _call_ai(
        self,
        *,
        system: str,
        user: str,
        schema: type[_ModelT],
        fallback: Callable[[dict[str, Any]], _ModelT],
    ) -> _ModelT:
        try:
            raw = self._capture(
                await self._ai.complete_json(system_prompt=system, user_prompt=user)
            )
        except AIProviderError as exc:
            logger.warning("AI provider failed for career pack: %s", exc)
            raise CareerPackError(
                "The AI helper is unavailable right now. Try again in a moment."
            ) from exc
        try:
            return schema.model_validate(raw.data)
        except ValidationError as exc:
            logger.warning(
                "AI returned malformed career-pack payload, using fallback: %s",
                exc,
            )
            return fallback(raw.data or {})

    # Fallbacks — return a best-effort shape so the student still sees
    # SOMETHING rather than a 500 when the model drifts off-schema.

    @staticmethod
    def _fallback_linkedin_generated(data: dict[str, Any]) -> LinkedInGenerated:
        return LinkedInGenerated(
            headline=str(data.get("headline") or "Student — open to internships"),
            about=str(data.get("about") or ""),
            education_entry=str(data.get("education_entry") or ""),
            project_entries=[
                LinkedInProjectSuggestion(
                    name=str(p.get("name") or "Project"),
                    description=str(p.get("description") or ""),
                )
                for p in (data.get("project_entries") or [])
                if isinstance(p, dict)
            ],
            skills=[str(s) for s in (data.get("skills") or []) if isinstance(s, str)],
            checklist=[
                str(c) for c in (data.get("checklist") or []) if isinstance(c, str)
            ],
        )

    @staticmethod
    def _fallback_linkedin_review(data: dict[str, Any]) -> LinkedInReview:
        return LinkedInReview(
            summary=str(data.get("summary") or "Review unavailable — try again."),
        )

    @staticmethod
    def _fallback_github_generated(data: dict[str, Any]) -> GitHubGenerated:
        return GitHubGenerated(
            username_suggestions=[
                str(s)
                for s in (data.get("username_suggestions") or [])
                if isinstance(s, str)
            ],
            bio=str(data.get("bio") or "Student developer.")[:160],
            profile_readme=str(data.get("profile_readme") or ""),
            project_readmes=[
                GitHubProjectReadme(
                    project_title=str(r.get("project_title") or "Project"),
                    filename=str(r.get("filename") or "README.md"),
                    body=str(r.get("body") or ""),
                )
                for r in (data.get("project_readmes") or [])
                if isinstance(r, dict)
            ],
            checklist=[
                str(c) for c in (data.get("checklist") or []) if isinstance(c, str)
            ],
        )

    @staticmethod
    def _fallback_github_review(data: dict[str, Any]) -> GitHubReview:
        return GitHubReview(
            profile_summary=str(
                data.get("profile_summary") or "Review unavailable — try again."
            ),
        )


# --- Status derivation --------------------------------------------------


def _status(pack: dict[str, Any], side: str, *, url: str | None) -> CareerStatus:
    """Derive missing / started / needs_improvement / completed.

    Rules (kept simple — the student can also mark it complete manually
    later, once we add that affordance):

      * no URL → missing
      * URL + no review yet → started
      * URL + a review with any suggestions → needs_improvement
      * explicitly set to 'completed' in the pack → completed
    """
    stored = pack.get(f"{side}_status")
    if stored == "completed":
        return "completed"
    if not url:
        return "missing"
    rec = pack.get(f"{side}_recommendations")
    if isinstance(rec, dict):
        if side == "linkedin":
            actionable = any(
                bool(rec.get(k))
                for k in (
                    "suggested_headline",
                    "suggested_about",
                    "missing_sections",
                    "skills_to_add",
                    "projects_to_improve",
                    "checklist",
                )
            )
        else:
            actionable = any(
                bool(rec.get(k))
                for k in (
                    "suggested_bio",
                    "suggested_profile_readme",
                    "project_readme_suggestions",
                    "repo_checklist",
                    "cv_projects_to_add",
                )
            )
        return "needs_improvement" if actionable else "started"
    return "started"


# --- Prompt helpers -----------------------------------------------------


def _user_prompt_generate(surface: str, context: str) -> str:
    return (
        f"Generate {surface} starter content from these student CV facts:\n"
        f"{context}\n\n"
        "Return JSON only."
    )
