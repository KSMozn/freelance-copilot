import sys

import pytest

from app.scripts import create_admin
from app.scripts.create_admin import validate_admin_password


def test_admin_password_policy_rejects_short_password() -> None:
    with pytest.raises(ValueError, match="at least 12 characters"):
        validate_admin_password("short")


def test_admin_password_policy_accepts_long_password() -> None:
    validate_admin_password("long-enough-password")


def test_non_interactive_admin_creation_requires_environment_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    with pytest.raises(SystemExit) as exc:
        create_admin.main()

    assert exc.value.code == 1
