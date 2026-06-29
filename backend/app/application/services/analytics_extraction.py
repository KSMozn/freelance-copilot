"""Pure helpers for extracting analytics facts from application snapshots.

Snapshots are the source of truth. Where the structured field doesn't exist
(yet — Phase 6 keeps the snapshot lean) we fall back to body-text parsing
against a fixed dictionary. Every function here is pure: same input → same
output, no IO. Easy to unit-test.
"""
from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

# --- Buckets ----------------------------------------------------------------

# (lower_inclusive, upper_inclusive, label) — labels must match the spec.
SCORE_BUCKETS: tuple[tuple[int, int, str], ...] = (
    (0, 49, "0-49"),
    (50, 64, "50-64"),
    (65, 79, "65-79"),
    (80, 100, "80-100"),
)

QUALITY_BUCKETS: tuple[tuple[int, int, str], ...] = (
    (0, 59, "0-59"),
    (60, 74, "60-74"),
    (75, 84, "75-84"),
    (85, 100, "85-100"),
)


def score_bucket_label(score: int | float | None) -> str | None:
    if score is None:
        return None
    s = int(round(float(score)))
    for lo, hi, label in SCORE_BUCKETS:
        if lo <= s <= hi:
            return label
    return None


def quality_bucket_label(score: int | float | None) -> str | None:
    if score is None:
        return None
    s = int(round(float(score)))
    for lo, hi, label in QUALITY_BUCKETS:
        if lo <= s <= hi:
            return label
    return None


# --- Budget extraction ------------------------------------------------------

BUDGET_BUCKETS_ORDER: tuple[str, ...] = (
    "unknown",
    "under_250",
    "250_500",
    "500_1000",
    "1000_3000",
    "3000_plus",
)

_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _parse_budget_max(text: str | None) -> float | None:
    """Return the largest number found in the budget string, or None.

    e.g. "fixed USD 3000-5000" → 5000.0. "USD 800" → 800.0. None / "" → None.
    """
    if not text:
        return None
    numbers = []
    for match in _NUMBER_RE.finditer(text):
        try:
            numbers.append(float(match.group(0).replace(",", "")))
        except ValueError:
            continue
    return max(numbers) if numbers else None


def budget_bucket(snapshot_job_budget: str | None) -> str:
    """Map the snapshot's job.budget string into one of the canonical buckets."""
    top = _parse_budget_max(snapshot_job_budget)
    if top is None:
        return "unknown"
    if top < 250:
        return "under_250"
    if top < 500:
        return "250_500"
    if top < 1000:
        return "500_1000"
    if top < 3000:
        return "1000_3000"
    return "3000_plus"


# --- Technology extraction --------------------------------------------------

KNOWN_TECHNOLOGIES: tuple[str, ...] = (
    "Python",
    "FastAPI",
    "PostgreSQL",
    "Docker",
    "Kubernetes",
    "React",
    "TypeScript",
    "Node.js",
    ".NET",
    "C++",
    "AI",
    "LLM",
    "RAG",
    "OpenAI",
    "Claude",
    "LangChain",
    "LangGraph",
    "Supabase",
    "AWS",
    "Azure",
    "GCP",
    "SQL",
    "API",
    "REST",
    "OAuth",
    "Stripe",
)


def _word_boundary_pattern(term: str) -> re.Pattern[str]:
    """Build a case-insensitive pattern that matches `term` only when neither
    neighbour is alphanumeric. Handles ".NET" and "C++" correctly because
    re.escape() neutralises the punctuation.
    """
    escaped = re.escape(term.lower())
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.IGNORECASE)


_TECH_PATTERNS: dict[str, re.Pattern[str]] = {
    term: _word_boundary_pattern(term) for term in KNOWN_TECHNOLOGIES
}


def _snapshot_value(snapshot: dict[str, Any] | None, *keys: str) -> Any:
    """Traverse a nested snapshot dict safely."""
    cur: Any = snapshot
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def extract_technologies(snapshot: dict[str, Any] | None) -> list[str]:
    """Return the list of known technologies referenced by the snapshot.

    Priority: structured fields first (job.technologies, proposal.required_skills,
    skill-like score breakdown keys), then a body-parse fallback against the
    `KNOWN_TECHNOLOGIES` dictionary.
    """
    if not snapshot:
        return []
    found: set[str] = set()

    # 1. Structured: snapshot.job.technologies
    job_tech = _snapshot_value(snapshot, "job", "technologies")
    if isinstance(job_tech, list):
        for item in job_tech:
            normal = _match_known_tech(str(item))
            if normal:
                found.add(normal)

    # 2. Structured: snapshot.proposal.required_skills
    proposal_skills = _snapshot_value(snapshot, "proposal", "required_skills")
    if isinstance(proposal_skills, list):
        for item in proposal_skills:
            normal = _match_known_tech(str(item))
            if normal:
                found.add(normal)

    # 3. Structured: skill-like keys inside the opportunity score breakdown
    breakdown = _snapshot_value(snapshot, "opportunity_score", "breakdown")
    if isinstance(breakdown, dict):
        for key in breakdown.keys():
            normal = _match_known_tech(str(key))
            if normal:
                found.add(normal)

    # 4. Fallback: parse the proposal body + job title using the known list
    haystacks: list[str] = []
    title = _snapshot_value(snapshot, "job", "title")
    if isinstance(title, str):
        haystacks.append(title)
    body = _snapshot_value(snapshot, "proposal", "body")
    if isinstance(body, str):
        haystacks.append(body)
    short = _snapshot_value(snapshot, "proposal", "short_body")
    if isinstance(short, str):
        haystacks.append(short)
    p_title = _snapshot_value(snapshot, "proposal", "title")
    if isinstance(p_title, str):
        haystacks.append(p_title)

    haystack = "\n".join(haystacks)
    for term, pattern in _TECH_PATTERNS.items():
        if pattern.search(haystack):
            found.add(term)
    return sorted(found)


def _match_known_tech(value: str) -> str | None:
    """If `value` (case-insensitive) is one of the known technologies, return
    the canonical-case version. Otherwise None.
    """
    norm = value.strip().lower()
    for term in KNOWN_TECHNOLOGIES:
        if term.lower() == norm:
            return term
    return None


# --- Domain extraction ------------------------------------------------------

KNOWN_DOMAINS: tuple[str, ...] = (
    "AI SaaS",
    "Enterprise SaaS",
    "Document Management",
    "Government",
    "FinTech",
    "Analytics",
    "Data Platforms",
    "Cloud Platforms",
    "Marketplace",
    "Marketing Ops",
)


def extract_domain(snapshot: dict[str, Any] | None) -> str | None:
    """Return the single most likely domain for this application.

    Priority: snapshot.job.business_domain → snapshot.analysis.business_domain
    → first known-domain substring in (proposal.body + job.title).
    """
    if not snapshot:
        return None

    direct = _snapshot_value(snapshot, "job", "business_domain")
    if isinstance(direct, str) and direct.strip():
        canonical = _canonical_domain(direct)
        if canonical:
            return canonical

    analysis_domain = _snapshot_value(snapshot, "analysis", "business_domain")
    if isinstance(analysis_domain, str) and analysis_domain.strip():
        canonical = _canonical_domain(analysis_domain)
        if canonical:
            return canonical

    # Fallback: body + title scan
    parts: list[str] = []
    title = _snapshot_value(snapshot, "job", "title")
    if isinstance(title, str):
        parts.append(title)
    body = _snapshot_value(snapshot, "proposal", "body")
    if isinstance(body, str):
        parts.append(body)
    haystack = "\n".join(parts).lower()
    for domain in KNOWN_DOMAINS:
        if domain.lower() in haystack:
            return domain
    return None


def _canonical_domain(value: str) -> str | None:
    norm = value.strip().lower()
    for d in KNOWN_DOMAINS:
        if d.lower() == norm or d.lower() in norm or norm in d.lower():
            return d
    return None


# --- Score readers ----------------------------------------------------------


def snapshot_opportunity_score(snapshot: dict[str, Any] | None) -> int | None:
    raw = _snapshot_value(snapshot, "opportunity_score", "score")
    if isinstance(raw, (int, float)):
        return int(raw)
    return None


def snapshot_quality_score(snapshot: dict[str, Any] | None) -> int | None:
    raw = _snapshot_value(snapshot, "proposal", "quality_score")
    if isinstance(raw, (int, float)):
        return int(raw)
    return None


def snapshot_job_budget_text(snapshot: dict[str, Any] | None) -> str | None:
    raw = _snapshot_value(snapshot, "job", "budget")
    if isinstance(raw, str):
        return raw
    return None


# --- Numeric helpers --------------------------------------------------------


def safe_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (ArithmeticError, ValueError, TypeError):
        return None
