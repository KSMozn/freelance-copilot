"""Unit tests for the email-coach heuristics (pure rules, no LLM).

Regression focus: "420-style" slang digit groups used to pass every rule —
the digit-count rule needs >=4 digits, the year rule only fires at the
local-part boundary, and the repeat rule needs 4+ repeats.
"""
from __future__ import annotations

from app.application.dto.student_dto import EmailCoachRequest
from app.application.services.student_coach_service import check_email


def _codes(email: str) -> set[str]:
    res = check_email(EmailCoachRequest(email=email, full_name=None))
    return {w.code for w in res.warnings}


def test_slang_number_embedded_is_flagged() -> None:
    # The original gap: 3 digits, mid-token, no repeats.
    assert "email_slang_number" in _codes("xx420x@gmail.com")


def test_slang_number_standalone_is_flagged() -> None:
    assert "email_slang_number" in _codes("sam69@gmail.com")


def test_year_run_does_not_trip_slang_rule() -> None:
    # "1969" is a maximal digit run — the "69" entry must not match inside it.
    codes = _codes("jane.smith1969@gmail.com")
    assert "email_slang_number" not in codes
    # The boundary-year rule still covers it.
    assert "email_year_or_birthdate" in codes


def test_ordinary_numbered_address_stays_clean() -> None:
    # jane.smith123 is a perfectly normal address; 123 is not slang and the
    # boundary-number rule may fire, but the slang rule must not.
    assert "email_slang_number" not in _codes("jane.smith123@gmail.com")


def test_plain_name_address_is_clean() -> None:
    res = check_email(EmailCoachRequest(email="jane.smith@gmail.com", full_name="Jane Smith"))
    assert res.warnings == []
