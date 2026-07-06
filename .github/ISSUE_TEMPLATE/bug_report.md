---
name: Bug report
about: Something is broken. The narrower the reproduction, the faster the fix.
title: "[Bug] "
labels: ["bug", "needs-review"]
assignees: []
---

## Goal

<!-- What is currently broken, in one sentence. -->

## User Story (what was happening)

> When I **[action]** as a **[student / admin]**, I expect **[expected]**, but instead
> **[actual]**.

## Reproduction Steps

<!-- Numbered steps a fresh reviewer can copy verbatim. -->

1.
2.
3.

## Expected vs Actual

**Expected:**

**Actual:**

## Environment

- Environment: [ ] local · [ ] production
- Browser + version:
- Device / viewport: [ ] desktop · [ ] mobile 375px · [ ] mobile 414px
- Affected user (email or anonymised ID, if applicable):
- Date / time of occurrence:

## Screenshots / Recording

<!-- Screenshot of the broken state, plus browser console if there's a red error. -->

## Backend Signal

<!--
  If this looks like a backend bug, attach the relevant log line from
  Cloud Run (search by request time). Redact any PII.
-->

## Acceptance Criteria (what "fixed" means)

- [ ]
- [ ]

## Testing Notes

- [ ] Reproduces on `main`.
- [ ] Fix does not regress the CV creation journey.
- [ ] Fix does not regress PDF or DOCX download.
- [ ] Console clean after fix.

## Risk Areas

<!-- Which adjacent flows could be affected by the fix itself? -->

## Severity

- [ ] `urgent` — production down, data loss, or students can't complete the wizard.
- [ ] high — a whole feature is broken but there's a workaround.
- [ ] medium — visible, annoying, not blocking.
- [ ] low — cosmetic or edge-case.
