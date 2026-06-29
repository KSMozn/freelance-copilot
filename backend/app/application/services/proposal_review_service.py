"""Deterministic proposal quality review.

Eight pure-function dimensions sum to 100. Each dimension also surfaces
warnings when it scores below its threshold, so the UI can show concrete
guidance instead of a single number.

The review is intentionally deterministic — re-running it never changes the
score for the same input. A future iteration can add an optional AI second
opinion layered on top.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.application.dto.proposal_dto import (
    ProposalReviewResult,
    QualityBreakdown,
)
from app.application.services.proposal_prompts import BANNED_PHRASES
from app.domain.entities.analysis import JobAnalysis as DomainAnalysis
from app.domain.entities.portfolio import Portfolio
from app.domain.entities.proposal import Proposal

# Per-dimension caps. Sum must equal 100.
MAX_SPECIFICITY = 20
MAX_RELEVANCE = 20
MAX_PORTFOLIO_EVIDENCE = 15
MAX_CLARITY = 15
MAX_BREVITY = 10
MAX_NON_GENERIC = 10
MAX_RISK_AWARENESS = 5
MAX_CALL_TO_ACTION = 5
assert (
    MAX_SPECIFICITY
    + MAX_RELEVANCE
    + MAX_PORTFOLIO_EVIDENCE
    + MAX_CLARITY
    + MAX_BREVITY
    + MAX_NON_GENERIC
    + MAX_RISK_AWARENESS
    + MAX_CALL_TO_ACTION
    == 100
)

# Heuristic regexes used for "specificity" — concrete nouns / numbers /
# acronyms / version markers tend to outnumber filler.
_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?(?:%|h|hrs|hours|days|weeks)?\b")
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,}[A-Z0-9]*\b")
_CODE_TOKEN_RE = re.compile(r"\b[a-z]+[A-Z][A-Za-z0-9]+\b")  # camelCase tokens
_BULLET_RE = re.compile(r"(?m)^\s*[-•*]\s+|\n\s*\d+[.)]\s+")

_RISK_KEYWORDS = (
    "scope",
    "acceptance",
    "risk",
    "milestone",
    "clarif",
    "deadline",
    "ambiguity",
    "fixed price",
    "data sample",
)

_CTA_PATTERNS = (
    r"\b(let'?s|happy to|available|share|schedule|book|call)\b",
    r"\bnext step\b",
    r"\bcalendar\b",
    r"\b\d+[- ]?(?:minute|min)\b",
)


def _norm(s: str) -> str:
    return s.strip().lower()


def _word_count(text: str) -> int:
    return len([w for w in re.findall(r"\S+", text)])


@dataclass(slots=True)
class _DimResult:
    score: int
    warnings: list[str]


def _score_specificity(body: str) -> _DimResult:
    """Count concrete signals: numbers, acronyms, code tokens, bullets."""
    numbers = len(_NUMBER_RE.findall(body))
    acronyms = len(_ACRONYM_RE.findall(body))
    code = len(_CODE_TOKEN_RE.findall(body))
    bullets = len(_BULLET_RE.findall(body))
    raw = numbers + acronyms + code + (bullets * 2)
    # 8+ specific signals saturates the dimension.
    score = min(MAX_SPECIFICITY, round((raw / 8.0) * MAX_SPECIFICITY))
    warnings: list[str] = []
    if score < MAX_SPECIFICITY * 0.5:
        warnings.append(
            "Opening or body lacks concrete specifics (numbers, acronyms, "
            "named tools) — consider naming the exact stack or constraints."
        )
    return _DimResult(score=score, warnings=warnings)


def _score_relevance(body: str, analysis: DomainAnalysis | None) -> _DimResult:
    """Fraction of the job's required skills the body actually mentions."""
    if analysis is None or not analysis.required_skills:
        return _DimResult(score=MAX_RELEVANCE // 2, warnings=[])

    body_l = body.lower()
    mentioned = 0
    for skill in analysis.required_skills:
        n = _norm(skill)
        if n and n in body_l:
            mentioned += 1
    ratio = mentioned / max(1, len(analysis.required_skills))
    score = round(ratio * MAX_RELEVANCE)
    warnings: list[str] = []
    if score < MAX_RELEVANCE * 0.5:
        warnings.append(
            "Proposal mentions fewer than half of the job's required skills — "
            "weave in 2–3 of the missing ones if you can do them honestly."
        )
    return _DimResult(score=min(MAX_RELEVANCE, score), warnings=warnings)


def _score_portfolio_evidence(
    body: str, portfolios: list[Portfolio]
) -> _DimResult:
    """Does the body name at least one of the user's portfolio projects?"""
    if not portfolios:
        return _DimResult(score=MAX_PORTFOLIO_EVIDENCE // 2, warnings=[])

    body_l = body.lower()
    hits = 0
    for p in portfolios:
        # Match by title or by the project's distinctive first 6 chars.
        if not p.title:
            continue
        if _norm(p.title) in body_l:
            hits += 1
            continue
        head = _norm(p.title)[:8]
        if head and head in body_l:
            hits += 1
    if hits == 0:
        return _DimResult(
            score=0,
            warnings=["Consider adding one concrete project reference from your portfolio."],
        )
    score = MAX_PORTFOLIO_EVIDENCE if hits >= 1 else 0
    return _DimResult(score=score, warnings=[])


def _score_clarity(body: str) -> _DimResult:
    """Readability heuristic — penalize very long sentences and walls of text."""
    sentences = [s for s in re.split(r"[.!?]+", body) if s.strip()]
    if not sentences:
        return _DimResult(score=0, warnings=["Body appears empty or unparseable."])
    avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
    paragraphs = [p for p in body.split("\n\n") if p.strip()]
    # Ideal: avg sentence length 12–22 words, ≥ 2 paragraphs.
    score = MAX_CLARITY
    warnings: list[str] = []
    if avg_len > 28:
        score -= 5
        warnings.append("Average sentence length is high — break long sentences.")
    elif avg_len > 22:
        score -= 2
    if avg_len < 6:
        score -= 4
        warnings.append("Sentences are very short — risk of sounding choppy.")
    if len(paragraphs) < 2:
        score -= 3
        warnings.append("Body is a single block — split into 2–3 paragraphs.")
    return _DimResult(score=max(0, score), warnings=warnings)


def _score_brevity(body: str) -> _DimResult:
    """Body word count should land in the 250–450 target band."""
    wc = _word_count(body)
    warnings: list[str] = []
    if 250 <= wc <= 450:
        return _DimResult(score=MAX_BREVITY, warnings=warnings)
    if 200 <= wc < 250 or 450 < wc <= 520:
        return _DimResult(
            score=int(MAX_BREVITY * 0.7),
            warnings=[f"Body is {wc} words; aim for 250–450."],
        )
    if 150 <= wc < 200 or 520 < wc <= 600:
        return _DimResult(
            score=int(MAX_BREVITY * 0.4),
            warnings=[f"Body is {wc} words; aim for 250–450."],
        )
    return _DimResult(
        score=0,
        warnings=[f"Body is {wc} words — far outside the 250–450 target."],
    )


def _score_non_generic(body: str, title: str | None) -> _DimResult:
    """Subtract for each banned phrase. Bonus if none are present."""
    haystack = (title or "") + "\n" + body
    haystack_l = haystack.lower()
    hits: list[str] = []
    for phrase in BANNED_PHRASES:
        if phrase.lower() in haystack_l:
            hits.append(phrase)
    if not hits:
        return _DimResult(score=MAX_NON_GENERIC, warnings=[])
    # -3 per banned phrase, floored at 0.
    score = max(0, MAX_NON_GENERIC - len(hits) * 3)
    warnings = [f'Generic phrase detected: "{p}"' for p in hits[:3]]
    return _DimResult(score=score, warnings=warnings)


def _score_risk_awareness(body: str, risk_notes: list[str]) -> _DimResult:
    """Does the proposal acknowledge scope / risk / acceptance / milestones?"""
    body_l = body.lower()
    keyword_hits = sum(1 for kw in _RISK_KEYWORDS if kw in body_l)
    has_explicit_notes = bool(risk_notes)
    score = 0
    warnings: list[str] = []
    if has_explicit_notes:
        score += 3
    score += min(2, keyword_hits)  # cap the keyword bonus
    if score == 0:
        warnings.append(
            "No explicit risk / scope acknowledgement — add a one-line caveat."
        )
    return _DimResult(score=min(MAX_RISK_AWARENESS, score), warnings=warnings)


def _score_call_to_action(body: str) -> _DimResult:
    body_l = body.lower()
    if any(re.search(p, body_l) for p in _CTA_PATTERNS):
        return _DimResult(score=MAX_CALL_TO_ACTION, warnings=[])
    return _DimResult(
        score=0,
        warnings=[
            "Closing lacks a low-friction next step (a call offer, a calendar, etc.)."
        ],
    )


class ProposalReviewService:
    """Stateless review engine. Constructed once per request from the DI layer."""

    def review(
        self,
        *,
        proposal: Proposal,
        analysis: DomainAnalysis | None,
        portfolios: list[Portfolio],
    ) -> ProposalReviewResult:
        results = {
            "specificity": _score_specificity(proposal.body),
            "relevance": _score_relevance(proposal.body, analysis),
            "portfolio_evidence": _score_portfolio_evidence(proposal.body, portfolios),
            "clarity": _score_clarity(proposal.body),
            "brevity": _score_brevity(proposal.body),
            "non_generic_wording": _score_non_generic(proposal.body, proposal.title),
            "risk_awareness": _score_risk_awareness(
                proposal.body, proposal.risk_notes
            ),
            "call_to_action": _score_call_to_action(proposal.body),
        }
        breakdown_dict = {k: v.score for k, v in results.items()}
        warnings: list[str] = []
        for r in results.values():
            warnings.extend(r.warnings)

        total = sum(breakdown_dict.values())
        return ProposalReviewResult(
            quality_score=total,
            quality_breakdown=QualityBreakdown(**breakdown_dict),
            warnings=warnings,
        )
