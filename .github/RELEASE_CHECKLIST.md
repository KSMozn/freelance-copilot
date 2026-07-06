# Careero — Release Smoke Test

Walk this checklist against the newly-deployed revision **before** telling anyone the
release is live. Any item that fails is a rollback candidate — see
`README_DEVELOPMENT_PROCESS.md` §5.3.

The whole list should take ~15 minutes. Do it in the primary Chrome profile, then
skim on Safari and mobile.

---

## 0. Deploy Sanity

- [ ] `gcloud run services list --region=europe-west1` shows the new revision serving
      100% of traffic for both `freelance-copilot-backend` and `-frontend`.
- [ ] Backend logs since deploy contain **no** `ERROR` or `Traceback` lines.
- [ ] `curl -sf https://api.careero.app/openapi.json | jq -r '.info.title'` returns
      the app title.

## 1. Student CV Creation Journey

- [ ] Landing at `https://app.careero.app` redirects to `/login`.
- [ ] Requesting an OTP delivers a real code to a test inbox.
- [ ] OTP verifies and lands on `/student`.
- [ ] Basics step saves full name + email + phone.
- [ ] Education step saves university + degree + major + graduation year.
- [ ] Photo step accepts a JPEG upload and shows the crop control.
- [ ] Skills / Courses / Projects / Internships / Volunteer / Languages / Certificates
      each accept a new entry and persist it (refresh the page → still there).
- [ ] Summary step generates a draft when clicked (LLM roundtrip completes < 15s).
- [ ] Preview step shows the CV HTML in the iframe.

## 2. CV Editing Journey

- [ ] Existing entry can be opened, edited, saved.
- [ ] Deleted entry disappears from CV preview immediately.
- [ ] Wizard resume — log out and back in, land on the last uncompleted step.
- [ ] Reset-wizard admin action clears the profile without error.

## 3. PDF Download

- [ ] Download button on Preview step returns a valid PDF (< 10s).
- [ ] Filename is `{full_name}.pdf`.
- [ ] Every populated section appears in the PDF.
- [ ] Empty sections do NOT appear as blank headings.
- [ ] Photo (if uploaded) renders inside its circular frame at the wizard's crop.

## 4. DOCX Download

- [ ] "Download CV" dropdown shows PDF + DOCX options.
- [ ] DOCX opens in Microsoft Word without a repair prompt.
- [ ] DOCX opens in Google Docs and renders cleanly.
- [ ] Circular photo renders inside the circle (no white ring, correct crop).
- [ ] `LinkedIn`, `GitHub`, `Portfolio` labels are clickable hyperlinks in Word.
- [ ] Modern template shows the dark navy sidebar; Creative shows the purple band.
- [ ] Filename is `{full_name}_CV.docx`.

## 5. Template Switching

- [ ] All 5 templates (classic, modern, minimal, academic, creative) preview
      correctly.
- [ ] "Set as default" persists the choice (refresh — still selected).
- [ ] Download uses whichever template is currently selected.

## 6. Internship Section

- [ ] "Add internship" opens the InternshipCard.
- [ ] Field dropdown selection shows 6 preset chips.
- [ ] Clicking a chip appends the task to Responsibilities AND removes the chip.
- [ ] Pool rotates in the next unused task from the 12-item pool.
- [ ] Action-verb chips (Tested / Analyzed / …) append `Verb ` to responsibilities.
- [ ] "Improve with AI" with 1-2 words of input → returns `vague=true` with follow-ups.
- [ ] "Improve with AI" with rich input → returns summary + 2-4 bullets.
- [ ] Editable summary + bullets persist after Save.
- [ ] Internship section appears in PDF and DOCX downloads.

## 7. Project Section

- [ ] Project entry accepts title, description, roles, tech stack, features,
      hardest part, URL.
- [ ] Preview renders projects as a narrative paragraph (not as bullets).
- [ ] "Tech stack" chips work.

## 8. AI Enhancement

- [ ] Proofread on Preview returns 0 or more fixes without crashing.
- [ ] Applying a fix updates the underlying field.
- [ ] Draft Summary produces a headline + summary that respect the profile.
- [ ] Coach Text tightens a project blurb without inventing new content.
- [ ] Coach Internship follows honesty rules (no fake tools / metrics).

## 9. LinkedIn Support

- [ ] Career Starter Pack step surfaces the LinkedIn card.
- [ ] "Create profile" walkthrough shows step-by-step instructions.
- [ ] "Improve profile" accepts a PDF upload and returns review notes.
- [ ] LinkedIn URL saves to `profile.links.linkedin`.
- [ ] LinkedIn appears as a clickable hyperlink on the CV DOCX.

## 10. GitHub Support

- [ ] Career Starter Pack step surfaces the GitHub card.
- [ ] Entering a GitHub username returns generated / review content.
- [ ] GitHub URL saves and renders on the CV.

## 11. Email Links (Deep-links)

- [ ] `https://app.careero.app/student?step=preview` lands directly on the Preview
      step (not on resume-from-last).
- [ ] `.../student?step=internships` lands on the Internships step.
- [ ] `.../student?step=starter-pack` lands on the Career Starter Pack.
- [ ] Unknown `?step=` value silently falls back to resume behaviour.
- [ ] Admin `Send Email` preview iframe renders every template with no `{placeholder}`
      literals left over.
- [ ] Sending a real test email arrives in Gmail with a working CTA button.

## 12. Mobile Responsiveness

Test in Chrome DevTools at **375px** viewport. Then eyeball at 414px.

- [ ] Wizard header + progress bar fit without overflow.
- [ ] Every step's form fields are tappable (48px minimum touch target).
- [ ] Combobox dropdowns don't clip off-screen.
- [ ] Preview step: CV preview scrolls within its container, doesn't overflow the page.
- [ ] "Download CV" menu opens without clipping the last option.
- [ ] Admin surface still opens at `?surface=admin` and renders the tables in
      horizontal-scroll mode.

## 13. Basic Performance

- [ ] Wizard cold-load lands under 3 seconds on a warm cache (Cloud Run cold-start
      may push first-request to 5s — acceptable, subsequent < 1s).
- [ ] CV preview HTML fetch < 2s.
- [ ] PDF generation < 10s for a full profile.
- [ ] DOCX generation < 5s for a full profile.
- [ ] `/admin/overview` renders under 3s with the current volume of data.

## 14. Production Environment Variables

- [ ] Backend startup log contains `Application startup complete.` without any
      "environment variable not set" warnings.
- [ ] `POST /api/v1/auth/request-code` returns 200 (OTP delivery uses `RESEND_API_KEY`).
- [ ] `POST /api/v1/students/coach/internship` returns 200 with a real internship
      payload (uses `OPENAI_API_KEY` + `OPENAI_BASE_URL`).
- [ ] `GET /api/v1/students/cv.pdf` returns 200 (WeasyPrint system libs present).
- [ ] `GET /api/v1/students/cv.docx` returns 200 (python-docx works).
- [ ] Photo upload succeeds (GCS bucket writable).
- [ ] Admin login succeeds at `https://admin.careero.app` (`JWT_SECRET_KEY` set).

## 15. Sign-off

- [ ] Rollback anchor recorded: backend previous revision =
      `___________________`, frontend previous = `___________________`.
- [ ] Release notes commented on each merged PR since the last release, or captured
      in a GitHub release tag (`gh release create`) with the commit SHA and any known
      issues.
- [ ] If any item above failed, opened an issue AND either rolled back or triggered
      a follow-up PR before closing the release.
