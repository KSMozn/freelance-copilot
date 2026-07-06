<!--
  Careero PR template. Fill in every section. Empty sections get PRs
  bounced back. Delete this comment before submitting.
-->

## Summary

<!-- One or two sentences. What does this PR do, and why? -->

## Related Issue

<!-- e.g. Closes #123, or "N/A - typo fix". -->

Closes #

## Type of Change

<!-- Check exactly one. -->

- [ ] `feature` — new user-facing capability
- [ ] `fix` — non-urgent bug fix
- [ ] `hotfix` — urgent production bug
- [ ] `chore` — refactor, docs, tooling, dependencies
- [ ] `ui` — visual / interaction change only

## Area

<!-- Check every area this touches. -->

- [ ] Frontend (student wizard)
- [ ] Frontend (admin panel)
- [ ] Backend API
- [ ] Database migration
- [ ] CV rendering (PDF)
- [ ] CV rendering (DOCX)
- [ ] AI prompts / coach services
- [ ] Email templates
- [ ] Authentication / JWT
- [ ] Environment variables / secrets
- [ ] CI / build tooling

## Screenshots

<!--
  REQUIRED for any UI change. Before/after, desktop + mobile.
  Drag images into this text box. Delete this section only if there is
  no visible change (backend-only PR).
-->

**Before:**

**After:**

**Mobile (375px):**

## Before / After Behaviour

<!--
  Describe what the app did before this change and what it does now.
  For a bug fix, include the exact reproduction steps.
-->

## How It Was Tested

<!--
  List the manual steps you actually ran. "It compiles" is not testing.
  Reference specific wizard steps, templates, browsers, etc.
-->

- [ ] Docker compose stack up, backend healthy.
- [ ] `npx tsc --noEmit` in `frontend/` passes.
- [ ] `pytest` in the backend container passes for touched modules.
- [ ] `npm run build` in `frontend/` succeeds.
- [ ] Registered a fresh student and walked the wizard end-to-end.
- [ ] Downloaded a PDF and opened it.
- [ ] Downloaded a DOCX and opened it in Word / Google Docs (if renderer changed).
- [ ] Mobile view (Chrome DevTools 375px) has no horizontal scroll or clipped
      buttons.
- [ ] Browser console has no red errors on the touched screens.
- [ ] Admin panel still renders (if the change touches shared state).

<!-- Add lines for anything not covered above. -->

## Risk Areas

<!--
  What could this break? Which flows should reviewers stress-test?
  Be honest. "No risk" is almost never true.
-->

## Reviewer Notes

<!--
  Anything the reviewer should know before opening the diff:
  - Is this stacked on another PR?
  - Is there a follow-up planned?
  - Is a specific reviewer being asked (e.g. Khaled for AI prompts)?
  - Any weird workaround or Chesterton's fence to preserve?
-->

## Checklist

- [ ] The linked issue's acceptance criteria are met.
- [ ] Branch is up to date with `main`.
- [ ] CI is green (or expected-green — flag known-flaky checks).
- [ ] `.env.example` updated if new env vars were added.
- [ ] Docs / comments updated if behaviour changed.
- [ ] No new lint warnings introduced.
- [ ] Only ONE concern in this PR (or explicitly justified above).
- [ ] Ready to squash-merge — no fixup commits or WIP left behind.
