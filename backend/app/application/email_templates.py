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
    "cv_incomplete_reminder": EmailTemplateSpec(
        id="cv_incomplete_reminder",
        name="Your first CV is almost ready",
        description=(
            "Nudges students who started the wizard but haven't finished "
            "back to complete their CV. Includes a Send Feedback link for "
            "students who got stuck."
        ),
        subject="Your {app_name} CV is almost ready",
        audience_hint=(
            "Best for students with wizard progress but who haven't reached "
            "the Preview step."
        ),
    ),
    "cv_download_reminder": EmailTemplateSpec(
        id="cv_download_reminder",
        name="Your CV is ready to download",
        description=(
            "Reminds students who finished the wizard but haven't downloaded "
            "their CV to pick a template and download. Highlights the 5 "
            "available CV templates."
        ),
        subject="Your {app_name} CV is ready to download",
        audience_hint=(
            "Best for students who reached the Preview step but haven't "
            "downloaded a CV (has_downloaded_cv=No)."
        ),
    ),
    "docx_availability_announcement": EmailTemplateSpec(
        id="docx_availability_announcement",
        name="Now available: CV in DOCX",
        description=(
            "One-off announcement — the CV can now be downloaded as an "
            "editable Word (.docx) file alongside the existing PDF. CTA "
            "opens the download page."
        ),
        subject="Your {app_name} CV is now available in DOCX",
        audience_hint=(
            "Any student who has used the wizard. Especially valuable for "
            "students who've already downloaded a PDF and might want an "
            "editable copy."
        ),
    ),
}


def get_template(template_id: str) -> EmailTemplateSpec | None:
    return EMAIL_TEMPLATES.get(template_id)


def list_templates() -> list[EmailTemplateSpec]:
    return list(EMAIL_TEMPLATES.values())
