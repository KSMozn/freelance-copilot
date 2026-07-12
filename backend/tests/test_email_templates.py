"""Guards for the admin-triggered email template registry.

Every registered template must ship both an .html and .txt body, and every
body + subject must render cleanly through the real str.format_map renderer
with the context admin_service builds — so a stray/malformed placeholder or a
missing file is caught here, not in a live send.
"""
from __future__ import annotations

import pytest

from app.application.email_templates import EMAIL_TEMPLATES
from app.infrastructure.email.template_renderer import _SafeDict, render

# Mirrors AdminService._build_template_context — every key a template may use.
_FULL_CONTEXT = {
    "first_name": "Sara",
    "full_name": "Sara Ahmed",
    "email": "sara@example.com",
    "app_name": "Careero",
    "app_url": "https://app.careero.app",
    "feedback_url": "https://app.careero.app/feedback",
    "college": "Cairo University",
    "major": "Computer Science",
    "graduation_year": "2027",
    "linkedin_url": "https://linkedin.com/in/sara",
    "github_url": "https://github.com/sara",
}


@pytest.mark.parametrize("template_id", sorted(EMAIL_TEMPLATES))
def test_template_renders_with_no_unresolved_placeholders(template_id: str) -> None:
    spec = EMAIL_TEMPLATES[template_id]
    subject = spec.subject.format_map(_SafeDict(_FULL_CONTEXT))
    html = render(f"{template_id}.html", _FULL_CONTEXT)
    text = render(f"{template_id}.txt", _FULL_CONTEXT)

    # A leftover "{first_name}" etc. means a placeholder the context doesn't
    # cover — either a typo'd token or a missing context key.
    for rendered in (subject, html, text):
        for key in _FULL_CONTEXT:
            assert "{" + key + "}" not in rendered, f"{template_id}: unresolved {{{key}}}"

    assert html.strip() and text.strip()
    assert spec.id == template_id
