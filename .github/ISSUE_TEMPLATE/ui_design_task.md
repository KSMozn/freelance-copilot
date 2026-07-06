---
name: UI / design task
about: Visual or interaction changes — layout, copy, empty states, mobile fixes.
title: "[UI] "
labels: ["ui", "frontend", "needs-review"]
assignees: []
---

## Goal

<!-- What visual outcome do we want, in one sentence. -->

## User Story

> As a **[student / admin]** on the **[screen]**, I want **[change]** so that
> **[reason]**.

## Design Reference

<!--
  REQUIRED. Attach one of:
  - Figma link (view-only is fine)
  - Screenshot from a competitor or an inspiration source
  - A rough sketch
  Explain what parts we're borrowing vs adapting.
-->

## Acceptance Criteria

- [ ] Screen matches the reference on desktop.
- [ ] Screen matches the reference on mobile (375px minimum viewport).
- [ ] Empty state (no data yet) renders cleanly, not as a blank block.
- [ ] Loading state (React Query pending) shows something, not a flash of empty.
- [ ] Error state has a clear message and an action (retry / go back).
- [ ] Copy is proofread — no lorem-ipsum leftovers.
- [ ] No layout shift when the page finishes loading.

## Screenshots / References

**Reference:**

**Current state:**

<!-- Add a screenshot of the current screen so reviewers see the delta. -->

## Testing Notes

- [ ] Chrome + Safari desktop.
- [ ] Chrome mobile emulator at 375px.
- [ ] Chrome mobile emulator at 414px.
- [ ] `prefers-color-scheme: dark` — does anything break?
- [ ] Screen reader tab-order is sensible (Tab through it once).
- [ ] Keyboard-only navigation works.

## Risk Areas

<!--
  Does this touch a shared component (Button, Card, Combobox)? Any
  other screen that reuses it needs to be checked.
-->

## Out of Scope

<!-- Optional. What we are NOT changing in this issue. -->
