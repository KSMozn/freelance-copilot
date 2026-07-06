---
name: Email template change
about: New admin-triggered template, or a change to an existing transactional email.
title: "[Email] "
labels: ["email-template", "backend", "needs-review"]
assignees: []
---

## Goal

<!--
  Which email are we changing, and what's the intended effect on the
  student (better conversion? clearer CTA? new announcement?).
-->

## Affected Template

- [ ] `linkedin_creation`
- [ ] `cv_incomplete_reminder`
- [ ] `cv_download_reminder`
- [ ] `docx_availability_announcement`
- [ ] `internship_availability_announcement`
- [ ] OTP login email
- [ ] Feedback confirmation email
- [ ] New template (proposed ID: __________________)

## User Story

> As a **student** who **[trigger condition]**, I should receive an email that
> **[expected content / CTA]** so that I can **[outcome]**.

## Design Reference

<!--
  For visual changes, attach the design mockup (Figma, image, or the
  designer's file). Confirm the design uses only email-safe HTML
  (tables, inline styles, no external CSS, no web fonts).
-->

## Copy

<!-- Paste the exact subject line and body copy. -->

**Subject:**

**Body (HTML rendering intent):**

**Body (plain-text `.txt` fallback):**

## Placeholders Used

<!--
  List every `{placeholder}` the template references. Confirm each
  one is populated by `_build_template_context` in `admin_service.py`.
-->

- [ ] `{first_name}`
- [ ] `{app_name}`
- [ ] `{app_url}`
- [ ] `{feedback_url}`
- [ ] Other: ______________

## Acceptance Criteria

- [ ] Template renders locally through `render(template_name, ctx)` with zero
      unresolved `{placeholder}` literals in the output.
- [ ] Plain-text `.txt` fallback exists and mirrors the HTML content.
- [ ] Every CTA button has an Outlook VML fallback
      (`<!--[if mso]><v:roundrect ...`) so it renders in Outlook.
- [ ] No inline HTML comments that contain `{placeholder}` values (they leak in
      Gmail).
- [ ] Registered in `EMAIL_TEMPLATES` in `email_templates.py`.
- [ ] Admin `Send Email` dropdown shows the template.
- [ ] Preview iframe in the admin panel renders the template with substituted
      placeholders.
- [ ] Test send arrives at a real inbox (Gmail + Outlook) and looks correct.
- [ ] Any `{app_url}/student?step=<slug>` deep-link routes to the right wizard step.

## Testing Notes

- [ ] Preview via admin `Send Email` modal.
- [ ] Send to a personal Gmail — check the CTA button + all links.
- [ ] Send to an Outlook / Hotmail if available.
- [ ] Confirm mobile Gmail rendering (Gmail iOS/Android app strips more than web).
- [ ] Confirm `usage_events` audit trail records the send with `template=<id>`
      and `target_user_id=<uid>` in meta.

## Risk Areas

- Placeholder leaks. A single unresolved `{placeholder}` in production is visible
  as literal text in the recipient's inbox.
- CTA button invisibility in Outlook — always test with VML fallback.
- Gmail's HTML comment parser strips inconsistently — never put a placeholder
  inside an HTML comment.
- Wrong deep-link (`?step=<slug>`) sends the student to the wrong wizard step,
  where they'll bounce.

## Rollout

- [ ] Send a self-test to the maintainer's inbox before enabling the template for
      bulk sends.
- [ ] Only after visual confirmation, offer the template in the admin dropdown.
