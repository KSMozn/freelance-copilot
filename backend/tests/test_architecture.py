"""Architecture guardrails — the layering rules from backend/CLAUDE.md, enforced.

These tests parse imports statically (ast — no runtime side effects) and fail
when new code violates the Clean Architecture direction:

    api → application → domain ← infrastructure

The known pre-existing violations in the live Careero services are pinned in
an explicit allowlist. The allowlist may only SHRINK: adding a new entry is a
review-blocking event, and a stale entry (module cleaned but not delisted)
also fails, so the ratchet stays honest in both directions.
"""
from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"

# Measured 2026-07. These application modules import app.infrastructure.db
# directly (ORM models or concrete SQLAlchemy repositories) — documented,
# deliberate debt (see backend/CLAUDE.md "Known layering debt"). New code
# must depend on domain repository interfaces wired via core/deps.py.
INFRA_DB_ALLOWLIST = {
    "admin_auth_service.py",
    "admin_service.py",
    "career_pack_service.py",
    "cv_template_service.py",
    "daily_report_service.py",
    "feedback_service.py",
    "refresh_token_manager.py",
    "student_coach_service.py",
    "student_cv_docx_renderer.py",
    "student_cv_renderer.py",
    "student_profile_service.py",
    "usage_event_service.py",
}


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def _violations(root: Path, forbidden_prefixes: tuple[str, ...], skip: set[str] | None = None):
    skip = skip or set()
    offenders: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if path.name in skip:
            continue
        for mod in _imports(path):
            if mod.startswith(forbidden_prefixes):
                offenders.append(f"{path.relative_to(APP.parent)} -> {mod}")
    return offenders


def test_domain_imports_nothing_outward() -> None:
    """domain/ is the leaf layer — it may not import any other app layer."""
    offenders = _violations(
        APP / "domain",
        ("app.application", "app.infrastructure", "app.api"),
    )
    assert not offenders, "domain/ must stay pure:\n" + "\n".join(offenders)


def test_application_does_not_import_api() -> None:
    offenders = _violations(APP / "application", ("app.api",))
    assert not offenders, "application/ must not import api/:\n" + "\n".join(offenders)


def test_infrastructure_does_not_import_application_or_api() -> None:
    offenders = _violations(APP / "infrastructure", ("app.application", "app.api"))
    assert not offenders, "infrastructure/ depends inward only:\n" + "\n".join(offenders)


def test_application_does_not_import_infrastructure_db() -> None:
    """New application code must not reach into ORM models / concrete repos.

    The allowlisted modules are the documented pre-existing exceptions.
    """
    offenders = _violations(
        APP / "application",
        ("app.infrastructure.db",),
        skip=INFRA_DB_ALLOWLIST,
    )
    assert not offenders, (
        "New application modules must depend on domain repository interfaces, "
        "not app.infrastructure.db (see backend/CLAUDE.md):\n" + "\n".join(offenders)
    )


def test_infra_db_allowlist_only_shrinks() -> None:
    """Every allowlisted module must still violate — else remove it from the list."""
    services = APP / "application" / "services"
    stale: list[str] = []
    for name in sorted(INFRA_DB_ALLOWLIST):
        path = services / name
        if not path.exists():
            stale.append(f"{name} (file no longer exists)")
            continue
        if not any(mod.startswith("app.infrastructure.db") for mod in _imports(path)):
            stale.append(f"{name} (no longer imports app.infrastructure.db — delist it)")
    assert not stale, "Ratchet the allowlist down:\n" + "\n".join(stale)
