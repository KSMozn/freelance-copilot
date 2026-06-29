"""Attach citations to a generated body.

Phase F MVP — deterministic substring matching: for each graph node we
know about (experience, project, repository, certificate, content item,
or skill), check whether its name appears in the generated body. If so,
attach a citation row.

This is intentionally dumb and fast — no LLM call, no embeddings — so
it ships today and is easy to reason about. Phase G can layer an
LLM-backed grounding pass on top when we have market signals to feed it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.experience import Experience
from app.domain.entities.output import Citation
from app.domain.entities.project import Project


@dataclass(slots=True)
class GraphSnapshot:
    """Light bundle of graph nodes the service can scan against.

    Caller assembles this once per generation so we don't fetch in here.
    `skills` is a list of (skill_id, canonical_name) tuples.
    """

    experiences: list[Experience]
    projects: list[Project]
    skills: list[tuple[UUID, str]]


_WORD_BOUNDARY = re.compile(r"\b")


class CitationService:
    """Pure citation attacher; no DB. Inject the snapshot."""

    def attach(self, *, body_markdown: str, graph: GraphSnapshot) -> list[Citation]:
        if not body_markdown:
            return []
        lower = body_markdown.lower()
        citations: list[Citation] = []
        seen: set[tuple[str, str]] = set()  # (evidence_type, evidence_id-or-label)

        # Experiences: cite if company or "company role" appears.
        for exp in graph.experiences:
            for needle in (exp.company, f"{exp.role} at {exp.company}"):
                if not needle:
                    continue
                idx = _find_phrase(lower, needle.lower())
                if idx >= 0:
                    key = ("experience", str(exp.id))
                    if key in seen:
                        continue
                    seen.add(key)
                    citations.append(
                        Citation(
                            claim=needle,
                            evidence_type="experience",
                            evidence_id=str(exp.id),
                            evidence_label=f"{exp.role} @ {exp.company}",
                            snippet=_snippet(body_markdown, idx, len(needle)),
                        )
                    )
                    break

        # Projects.
        for proj in graph.projects:
            if not proj.name:
                continue
            idx = _find_phrase(lower, proj.name.lower())
            if idx >= 0:
                key = ("project", str(proj.id))
                if key in seen:
                    continue
                seen.add(key)
                citations.append(
                    Citation(
                        claim=proj.name,
                        evidence_type="project",
                        evidence_id=str(proj.id),
                        evidence_label=proj.name,
                        snippet=_snippet(body_markdown, idx, len(proj.name)),
                    )
                )

        # Skills — only worth surfacing the strongest hits to avoid noise.
        for skill_id, name in graph.skills:
            if not name:
                continue
            idx = _find_phrase(lower, name.lower())
            if idx < 0:
                continue
            key = ("skill", str(skill_id))
            if key in seen:
                continue
            seen.add(key)
            citations.append(
                Citation(
                    claim=name,
                    evidence_type="skill",
                    evidence_id=str(skill_id),
                    evidence_label=name,
                    snippet=_snippet(body_markdown, idx, len(name)),
                )
            )

        # Cap so the UI doesn't drown in chips.
        return citations[:20]


def _find_phrase(haystack_lower: str, needle_lower: str) -> int:
    """Word-boundary substring match. Returns -1 when missing."""
    if not needle_lower:
        return -1
    # ``re.search`` with \b is slow against many needles; fall back to ``find``
    # plus a manual boundary check for performance.
    start = haystack_lower.find(needle_lower)
    while start != -1:
        end = start + len(needle_lower)
        before_ok = start == 0 or not haystack_lower[start - 1].isalnum()
        after_ok = end == len(haystack_lower) or not haystack_lower[end].isalnum()
        if before_ok and after_ok:
            return start
        start = haystack_lower.find(needle_lower, start + 1)
    return -1


def _snippet(body: str, idx: int, needle_len: int, *, radius: int = 60) -> str:
    """A short surrounding excerpt for the UI to render."""
    start = max(0, idx - radius)
    end = min(len(body), idx + needle_len + radius)
    excerpt = body[start:end].strip().replace("\n", " ")
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(body) else ""
    return f"{prefix}{excerpt}{suffix}"
