---
name: AI prompt improvement
about: Tweak a coach prompt, honesty rule, or LLM response shape.
title: "[AI] "
labels: ["ai", "backend", "needs-review"]
assignees: []
---

## Goal

<!--
  Which prompt are we changing, and what problem does the change
  solve? (e.g. "internship coach hallucinated a company name" or
  "proofread misses passive-voice bullets").
-->

## Affected Prompt

<!-- Pick one. -->

- [ ] Internship coach (`_INTERNSHIP_COACH_SYSTEM` in `student_coach_service.py`)
- [ ] Project text coach (`improve_text` in `student_coach_service.py`)
- [ ] Volunteer text coach (`improve_text` in `student_coach_service.py`)
- [ ] Summary coach (`improve_text` — `field=summary`)
- [ ] Photo coach (`_PHOTO_SYSTEM_PROMPT` in `student_coach_service.py`)
- [ ] Proofread (`proofread` in `student_coach_service.py`)
- [ ] Draft summary (`draft_summary` in `student_coach_service.py`)
- [ ] LinkedIn generate / review (`career_pack_service.py`)
- [ ] GitHub generate / review (`career_pack_service.py`)
- [ ] Other:

## User Story

> As a **student**, when I **[action]**, the coach should **[expected behaviour]**
> instead of **[current behaviour]**.

## Sample Inputs and Current Outputs

<!--
  Copy 2-3 real (or realistic) student inputs and the current LLM
  output. Redact PII.
-->

**Input 1:**

```
```

**Current output:**

```
```

**Input 2:**

```
```

**Current output:**

```
```

## Desired Output

<!--
  What should the LLM produce for those same inputs after the change?
-->

## Acceptance Criteria

- [ ] The new prompt still contains the honesty rules (no inventing facts).
- [ ] The strict JSON output shape is unchanged, OR the DTO + frontend consumer +
      tests are updated in the same PR.
- [ ] Vague-input path (follow-up questions) still fires when the student's input
      is genuinely thin.
- [ ] Deterministic fallback still returns something usable if the LLM is
      unavailable (no crash, no empty section).
- [ ] Rich input produces the expected polished output (attach 2-3 transformations
      to the PR).
- [ ] Sparse input does not produce hallucinated content (attach a sparse-input
      test case to the PR).

## Testing Notes

- [ ] Local docker stack with real OpenAI key (or Groq) configured.
- [ ] Sample 5 varied inputs, including one deliberately vague.
- [ ] Confirm CV render (PDF + DOCX) uses the new output correctly.
- [ ] Admin activity shows the new `coach.*` usage event with expected meta.

## Risk Areas

<!--
  - Could this change break the frontend consumer's parsing?
  - Could it produce outputs that fail moderation?
  - Could it inflate token cost significantly?
-->
