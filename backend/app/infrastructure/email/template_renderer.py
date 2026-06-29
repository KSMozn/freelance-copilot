from __future__ import annotations

from pathlib import Path
from typing import Any

TEMPLATES_DIR = Path(__file__).parent / "templates"


def render(template_name: str, context: dict[str, Any]) -> str:
    """Render a template using Python's ``str.format_map``.

    Templates live alongside this module under ``templates/``. We deliberately
    avoid Jinja2 here — the only variable substitutions we need today are
    simple placeholders like ``{code}`` and ``{app_name}``. If templates grow
    conditionals or loops, swap this for Jinja2 in one place.
    """
    path = TEMPLATES_DIR / template_name
    raw = path.read_text(encoding="utf-8")
    return raw.format_map(_SafeDict(context))


class _SafeDict(dict):
    """Leaves unknown ``{key}`` placeholders untouched instead of raising.

    Avoids accidentally interpreting curly braces in user-supplied content as
    template variables.
    """

    def __missing__(self, key: str) -> str:  # pragma: no cover - trivial
        return "{" + key + "}"
