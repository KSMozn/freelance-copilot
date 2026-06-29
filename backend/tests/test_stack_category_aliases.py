"""Regression tests for ``StackRequirementSchema.category`` alias normalization.

LLMs (especially via the cheaper / faster providers) reliably slip on
singular/plural and stylistic variants. The Pydantic schema normalizes
these before the ``Literal`` check so one near-miss row doesn't bin the
whole analysis. This file pins the aliases we accept.
"""
import pytest
from pydantic import ValidationError

from app.application.dto.analysis_dto import StackRequirementSchema


@pytest.mark.parametrize(
    "raw, expected",
    [
        # Singular/plural slips (the bug that triggered the fix)
        ("integration", "integrations"),
        ("databases", "database"),
        # Casing + whitespace
        ("  Integrations  ", "integrations"),
        ("Tech_Stack", "tech_stack"),
        # Hyphens vs underscores
        ("nice-to-have", "nice_to_have"),
        ("ci/cd", "devops"),
        # Common abbreviations LLMs use
        ("auth", "authentication"),
        ("db", "database"),
        ("llm", "ai_llm"),
        ("infra", "devops"),
        ("cloud", "cloud_platform"),
        ("framework", "tech_stack"),
        # Canonical values pass through untouched
        ("tech_stack", "tech_stack"),
        ("security", "security"),
    ],
)
def test_category_alias_normalizes(raw: str, expected: str) -> None:
    payload = StackRequirementSchema(category=raw, name="x", importance=3)
    assert payload.category == expected


def test_unknown_category_still_raises() -> None:
    """No silent fallback — truly unknown labels still bubble up so we
    notice when the LLM invents a brand-new category we should adopt."""
    with pytest.raises(ValidationError):
        StackRequirementSchema(category="literally_made_up", name="x", importance=3)
