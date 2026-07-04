"""Admin-triggered email templates.

Registry of templates the admin panel can send on demand. Each entry
declares its human label, description, subject line, and target audience
hint. Body files live in `app/infrastructure/email/templates/{id}.html`
and `{id}.txt` and go through the existing str.format_map renderer.

Adding a new template:
  1. Drop `{id}.html` + `{id}.txt` in the templates dir.
  2. Add an EmailTemplateSpec entry below with a unique id.
  3. If new placeholders are needed, extend `_build_template_context`
     in `admin_service.py` so every field the template references is
     populated (missing keys leave `{key}` literal in the output).
"""
from __future__ import annotations

from pydantic import BaseModel


class EmailTemplateSpec(BaseModel):
    id: str
    name: str
    description: str
    subject: str
    audience_hint: str | None = None


EMAIL_TEMPLATES: dict[str, EmailTemplateSpec] = {
    "linkedin_creation": EmailTemplateSpec(
        id="linkedin_creation",
        name="Build Your First LinkedIn Profile",
        description=(
            "Encourages students without a LinkedIn profile to create one "
            "from their CV, step by step."
        ),
        subject="Build Your First LinkedIn Profile with {app_name}",
        audience_hint="Best for students without a LinkedIn URL on their CV.",
    ),
}


def get_template(template_id: str) -> EmailTemplateSpec | None:
    return EMAIL_TEMPLATES.get(template_id)


def list_templates() -> list[EmailTemplateSpec]:
    return list(EMAIL_TEMPLATES.values())
