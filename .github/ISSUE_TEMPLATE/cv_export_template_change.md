---
name: CV export / template change
about: PDF template edit, DOCX renderer change, or new CV template.
title: "[CV] "
labels: ["cv-export", "backend", "needs-review"]
assignees: []
---

## Goal

<!--
  Which template / renderer are we changing, and what visual or
  structural outcome do we want?
-->

## Affected Path

- [ ] PDF template `classic.html`
- [ ] PDF template `modern.html`
- [ ] PDF template `minimal.html`
- [ ] PDF template `academic.html`
- [ ] PDF template `creative.html`
- [ ] DOCX renderer (`student_cv_docx_renderer.py`)
- [ ] Renderer context (`student_cv_renderer.py` — `build_context`, `_entry_to_view`)
- [ ] Section order (`_SECTION_ORDER`) — [ ] `pdf-export` [ ] `docx-export`
- [ ] Photo transform (`_make_circular_photo`)
- [ ] New CV template (specify slug: __________________)

## User Story

> As a **student** using the **[template]** template, I want the **[section /
> visual element]** to **[change]** so that **[outcome]**.

## Design Reference

<!--
  For visual changes, attach a before/after mockup. For structural
  changes (new entry kind, reordered sections), sketch the section
  order.
-->

## Acceptance Criteria

- [ ] Change renders correctly in the PDF output.
- [ ] Change renders correctly in the DOCX output (Word AND Google Docs).
- [ ] All 5 PDF templates still render for a rich profile without crashing.
- [ ] Empty sections still skip (a section with 0 items produces no heading).
- [ ] Partial profile (Basics + Education only) renders without empty section
      headings.
- [ ] Photo (when present) fills the circle at any offset/zoom.
- [ ] Hyperlinks in the DOCX are clickable (LinkedIn, GitHub, Portfolio).
- [ ] Section order matches `_SECTION_ORDER` in both PDF and DOCX.
- [ ] If a new `student_entry_kind` value is introduced:
  - [ ] Postgres enum migration
  - [ ] Python `STUDENT_ENTRY_KINDS` tuple in `student_profile.py`
  - [ ] DTO `STUDENT_ENTRY_KINDS` Literal in `student_dto.py`
  - [ ] Section entry in `_SECTION_ORDER`
  - [ ] Rendering branch in every PDF template
  - [ ] Rendering branch in the DOCX renderer
  - Everything above lands in the SAME PR.

## Testing Notes

- [ ] Download PDF for each of the 5 templates and open all five.
- [ ] Download DOCX for each of the 5 templates and open all five in Word.
- [ ] Repeat DOCX opens in Google Docs — they diverge on some Word features.
- [ ] Rich profile (all sections populated) — no crashes, no missing entries.
- [ ] Partial profile (Basics + Education only) — no empty section headings.
- [ ] Profile with photo AND without photo — both render cleanly.
- [ ] Mobile preview (in the wizard's Preview step) fits the viewport.
- [ ] `pytest backend/tests/test_student_cv_docx_renderer.py` still green.

## Risk Areas

- CV rendering is the product's single point of failure. Every existing student's
  next download hits this path.
- PDF and DOCX have different code paths — a bug in one can be invisible in the
  other.
- Google Docs is stricter than Word on some Open Office XML constructs — always
  test both.
- ATS parsers walk the DOCX in reading order — introducing sidebars, floating
  shapes, or text boxes will silently break ATS-friendliness.

## Rollback Plan

<!--
  If this change breaks something in production, how do we recover?
  - Previous backend revision ID (fill in during release)
  - Any manual data cleanup needed?
-->
