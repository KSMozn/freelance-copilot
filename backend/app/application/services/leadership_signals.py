"""Detect leadership + soft-skill signals in a job posting + score the fit.

Pure functions. No DB, no provider calls — just text + a user_skills snapshot.

We intentionally keep the keyword lists tight and well-known. The point of
these dimensions is to gracefully *abstain* (return ``None``) when the
posting doesn't carry leadership / soft signals at all — a NULL leadership_fit
on an IC role is the correct outcome, not a 0.
"""
from __future__ import annotations

from app.domain.entities.user_skill import UserSkillEntry

# Phrases that signal leadership scope. Lowercased for matching.
LEADERSHIP_SIGNALS = (
    "manage", "manager", "managing", "management",
    "lead a team", "lead the team", "team lead",
    "mentor", "mentoring", "coaching",
    "stakeholder", "stakeholders", "executive",
    "hiring", "hire", "headcount",
    "roadmap", "strategy", "strategic direction",
    "cross-team", "cross-functional",
    "performance review", "performance management",
    "1:1", "one-on-one", "one to one",
    "delegating", "delegation",
    "director", "vp", "head of", "tech lead", "engineering lead",
)

SOFT_SKILL_SIGNALS = (
    "communication", "communicate", "communicator",
    "presentation", "present",
    "writing", "written communication",
    "stakeholder management",
    "collaboration", "collaborate", "collaborative",
    "empathy", "empathetic",
    "conflict resolution",
    "negotiation",
    "facilitation", "facilitate",
    "client-facing", "customer-facing",
    "remote-first", "remote",
    "ownership", "self-starter",
)


def detect_leadership_demand(*, description: str | None, required_skills: list[str]) -> bool:
    """Does this job actually demand leadership signals worth scoring?"""
    haystack = _flatten(description, required_skills)
    return any(token in haystack for token in LEADERSHIP_SIGNALS)


def detect_soft_demand(*, description: str | None, required_skills: list[str]) -> bool:
    haystack = _flatten(description, required_skills)
    return any(token in haystack for token in SOFT_SKILL_SIGNALS)


def score_category_fit(
    *,
    user_skills: list[UserSkillEntry],
    catalog_categories: dict[str, str],
    target_categories: set[str],
) -> int:
    """0..100 score for "how strong is the user in these catalog categories?"

    Uses proficiency as the per-row weight. A user with three proficiency-5
    leadership skills scores near the cap; an empty user gets 0.

    `catalog_categories` maps skill_id (as string) to category — caller
    provides this so we don't import the repo here.
    """
    if not user_skills:
        return 0
    relevant = [
        row
        for row in user_skills
        if catalog_categories.get(str(row.skill_id)) in target_categories
    ]
    if not relevant:
        return 0
    # Sum of proficiencies, normalized. Five proficiency-5 skills caps it.
    total = sum(min(5, max(1, row.proficiency)) for row in relevant)
    cap = 25  # 5 skills × prof 5 — anything above is full marks
    pct = min(100, round(100 * total / cap))
    return pct


def _flatten(description: str | None, required_skills: list[str]) -> str:
    parts: list[str] = []
    if description:
        parts.append(description)
    parts.extend(required_skills or [])
    return " \n ".join(parts).lower()
