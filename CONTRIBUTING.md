# Contributing to Careero

Careero is a web app that helps students create their first professional CV. It's a
small project with a small team — this guide keeps everyone aligned without turning
contribution into paperwork. Read it once, keep it open in a tab.

---

## 1. Project Overview

Careero is a student-only CV builder.

| Layer | Stack |
|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind, react-query |
| Backend | Python 3.13, FastAPI, SQLAlchemy async, Pydantic v2 |
| Database | PostgreSQL 16 (+ pgvector) |
| PDF | WeasyPrint (Jinja2 templates) |
| DOCX | python-docx (programmatic) |
| Auth | JWT, OTP email login |
| AI | OpenAI-compatible API (Groq in prod) |
| Email | Resend (`noreply@personaarmory.com`) |
| Hosting | Google Cloud Run + Cloud SQL + GCS, Cloudflare DNS |

Current scope is **student-only**. Every product decision goes through the student CV
journey: register → wizard → preview → download.

---

## 2. Who Can Contribute

- **Maintainer:** Khaled — final approver for user-facing product changes.
- **Team contributors:** invited collaborators with push access to feature branches only
  (no direct pushes to `main`).
- **External contributors:** open a fork PR from `main`, follow this document.

Every contributor should have:
- A GitHub account with 2FA enabled.
- Docker Desktop (or Colima) installed.
- Node 22+, Python 3.13+.
- Familiarity with the CV creation journey before touching anything on it.

---

## 3. Local Setup

```bash
git clone <repo-url>
cd <repo-dir>

# 1. Environment
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env       # only if present
# Ask Khaled for OPENAI_API_KEY, RESEND_API_KEY, SECRET_KEY.

# 2. Start the stack
docker compose up -d

# 3. Apply migrations (optional — the backend container already runs
#    `alembic upgrade head` on start; rerun manually only if you need to)
docker compose exec backend alembic upgrade head

# 4. Seed a local admin user
docker compose exec \
  -e ADMIN_EMAIL=you@example.com \
  -e ADMIN_PASSWORD='strong-password' \
  -e ADMIN_FULL_NAME='Your Name' \
  backend python -m app.scripts.create_admin

# 5. Verify
open http://localhost:5173             # student surface
open "http://localhost:5173/?surface=admin"   # admin surface
```

Health check: `curl http://localhost:8000/openapi.json | jq '.info.title'`.

### Environment Variables

Never commit real secrets. `backend/.env.example` lists every variable the backend reads,
with placeholder values. Add new variables there whenever the code starts consuming a
new key, in the same PR. Real values live in Secret Manager (prod) and `backend/.env`
(local, git-ignored).

Sensitive keys — `OPENAI_API_KEY`, `SECRET_KEY`, `POSTGRES_PASSWORD`, `RESEND_API_KEY` —
are fetched from GCP Secret Manager at runtime in prod. Rotating them is a maintainer
task; do not put real values in commits, in issues, or in any chat.

---

## 4. Branch Naming

We follow **GitHub Flow**. `main` is always production-ready. Branch off `main`, ship a
PR, delete the branch after merge.

| Prefix | Purpose | Example |
|---|---|---|
| `feature/` | New user-facing capability | `feature/internship-section` |
| `fix/` | Bug fix (non-urgent) | `fix/docx-hyperlink-color` |
| `chore/` | Refactor, docs, tooling, deps | `chore/upgrade-vite-6` |
| `hotfix/` | Urgent production bug | `hotfix/login-500` |

- Keep names lowercase, kebab-case, under ~50 characters.
- One branch = one focused change.
- Rebase or merge `main` into your branch before requesting review if it's behind.

**Never push directly to `main`.** Branch protection blocks it; try it once and you'll
get a rejected push.

---

## 5. Issue Creation

Every meaningful change starts as a GitHub issue.

1. Pick the right template (`.github/ISSUE_TEMPLATE/`):
   - **Feature request** — new capability
   - **Bug report** — something broken
   - **UI/design task** — visual work
   - **AI prompt improvement** — coach / renderer prompt edits
   - **CV export/template change** — PDF, DOCX, or template style
   - **Email template change** — admin-triggered or transactional email
2. Fill in the goal, user story, and acceptance criteria. If you can't state acceptance
   criteria, the issue isn't ready yet.
3. Add labels (see §12).
4. Assign yourself if you plan to do it.

Small typo fixes or one-line tweaks don't need an issue — a PR is enough.

---

## 6. Pull Request Process

1. **Branch off `main`.** Never off another feature branch.
2. **Keep PRs small.** Aim for < 400 lines diff. Split large features into a stack:
   backend → frontend types → UI. Reviewers will push back on anything that touches
   more than one concern at once.
3. **Open the PR early**, even as a draft, if you want directional feedback.
4. **Fill in the PR template** (`.github/pull_request_template.md`). Every field
   matters — the reviewer uses it as the starting point.
5. **Attach screenshots for any UI change.** Before/after, plus mobile view if the
   change is visible in the student wizard or admin panel.
6. **Squash-merge.** Keeps `main` history clean. GitHub is configured to default to
   squash — leave that setting.
7. **Delete the branch** after merge.

### PR must contain

- A working build (CI green).
- No lint or type errors.
- Tests for new backend logic when it has branches worth guarding.
- A description of manual testing done.
- A note on risk areas — what could this break?
- A link to the issue it closes (`Closes #123`), when applicable.

### PRs that need extra care

Anything touching these areas: **the CV builder, CV templates, PDF export, DOCX export,
AI prompts, email templates, authentication, environment variables, or production
deployment**. Khaled must approve these. See §7.

---

## 7. Code Review Rules

- **Every PR needs at least one approving review** before it can merge. GitHub branch
  protection enforces this.
- **Khaled must approve** any PR touching a path listed in `.github/CODEOWNERS`
  (CV builder, renderers, AI prompts, email templates, auth, migrations, config,
  deploy tooling). GitHub auto-requests his review on those paths and blocks the
  merge until he approves.
- **PRs that don't touch a CODEOWNERS-listed path** can be approved and merged by
  any trusted reviewer with push access — you don't need to wait for Khaled on a
  frontend copy tweak or a docs typo.
- **Approvals dismiss on new commits.** If you push after approval, the reviewer must
  re-approve. This is intentional — don't route around it.
- **All review comments must be resolved** before merging. "Resolved" means the author
  addressed them and clicked Resolve, or the reviewer clicked Resolve after being
  satisfied.
- **Reviewers focus on:** correctness, safety, blast radius, does it match the issue's
  acceptance criteria. Style is a nit — flag it if you want, but don't block on it.

Aim to leave the first review within 24 hours (business days). If you can't, say so on
the PR so the author can ping someone else.

---

## 8. UI Review Expectations

For any PR that changes what a user sees:

- **Screenshots or a short screen recording** in the PR description. Before and after,
  desktop and mobile (Chrome DevTools 375px minimum).
- **Walk the golden path in a browser** before requesting review. Don't rely on TS
  compile + tests to prove UI works.
- **Check the affected wizard step end-to-end** — resume, save, download, refresh.
- **Test with a partial profile** (student who's only done Basics + Education). Empty
  states must render cleanly, never as blank sections.
- **Check the admin panel** if the change affects data admins see (wizard funnel,
  users table, activity kinds, email templates).

If the change reworks a wizard step, include a note in the PR on how the new step
integrates with the auto-mark-done logic in
`frontend/src/features/student-wizard/StudentWizardPage.tsx`.

---

## 9. Testing Checklist

Every PR runs through this before requesting review:

- [ ] `docker compose up -d` and the app boots without errors.
- [ ] `npx tsc --noEmit` in `frontend/` passes.
- [ ] `pytest` in the backend container passes for touched modules.
- [ ] `npm run build` in `frontend/` succeeds (catches Vite issues type-check misses).
- [ ] CV creation still works (register a fresh student, hit each step of the wizard).
- [ ] CV editing still works (open an existing entry, edit, save, verify persisted).
- [ ] PDF download works and the file opens.
- [ ] DOCX download works and the file opens in Word or Google Docs — **if the change
      touches CV rendering, template files, or the DOCX renderer**.
- [ ] Template switching works — **if the change touches the CV renderer or template
      files**.
- [ ] AI enhancement works — **if the change touches coach endpoints or prompts**.
- [ ] Mobile view (375px) has no horizontal scroll and all buttons are tappable.
- [ ] Browser console shows no red errors on the touched screens.
- [ ] `.env.example` mentions any new environment variable the code now reads.

The full pre-release checklist lives at `.github/RELEASE_CHECKLIST.md` — that's the
release gate, not the per-PR gate.

---

## 10. Definition of Done

A PR is done when:

- [ ] All acceptance criteria in the linked issue are met.
- [ ] The testing checklist (§9) is complete.
- [ ] The code has at least one approving review.
- [ ] All review comments are resolved.
- [ ] CI is green.
- [ ] The branch is up to date with `main`.
- [ ] Screenshots (for UI) are in the PR description.
- [ ] Any new env var, migration, or dependency is documented in the PR body.
- [ ] The issue is closed by the PR (`Closes #N`) or explicitly marked as follow-up.

Definition of Done for a **feature** additionally requires:
- The feature works for a partial-profile student (empty states clean).
- The feature has a mobile view.
- If admin-facing metrics are relevant, the admin panel reflects them.

---

## 11. Deployment Rules

- **`main` is production-ready at all times.** If you can't say yes to that, don't
  merge.
- **Only Khaled deploys to production.** Contributors request a deploy by commenting
  on the merged PR — Khaled picks up the queue.
- **Every prod deploy** follows the sequence documented in
  `README_DEVELOPMENT_PROCESS.md`: build backend → run migration job → roll backend →
  build frontend → roll frontend → smoke test.
- **Migrations run before the code that needs them.** Never merge a PR that ships code
  requiring a migration without shipping the migration in the same PR.
- **Never skip the migrate job** even if you think no schema changed — it's a no-op
  when there's nothing to do.
- **Rollback anchors** are always the previous revision id (visible in `gcloud run
  revisions list`). Note them in the PR description when the change is risky.

---

## 12. Labels

Use the labels in `.github/LABELS.md`. In short:

- **Type:** `feature`, `bug`, `chore`, `ui`, `ai`
- **Area:** `frontend`, `backend`, `cv-export`, `docx-export`, `pdf-export`,
  `email-template`, `linkedin`, `github-profile`, `internship`
- **Priority / state:** `urgent`, `good-first-issue`, `needs-review`,
  `ready-for-testing`, `blocked`

At minimum, every issue and PR gets one type label and one area label.

---

## 13. Communication

- **Async first, GitHub-native.** All discussion lives on the PR or issue thread.
  Others need to see it, and it becomes searchable history.
- **For urgent production issues** (site down, data loss risk), open a `hotfix/`
  branch immediately and mention the maintainer directly on the resulting PR — that's
  the fastest signal path.
- **Weekly rhythm** — see `README_DEVELOPMENT_PROCESS.md`.
- **Never share prod credentials, JWTs, or user emails in issues or PRs.** Use
  Secret Manager and the admin panel.
- **When you don't know, ask.** Comment on the relevant issue or open a new one
  with the `question` label. Better a one-line question than a wrong assumption
  merged into `main`.

---

## 14. Security and Privacy

- **Student data is real.** Prod has actual students' CVs, emails, and phone numbers.
  Never copy a prod database dump to your laptop. If you need realistic data, seed a
  local student via the wizard.
- **Never log PII.** Emails and phone numbers should not be in structured logs.
  `usage_events.meta` should hold IDs and enum kinds, not free-text profile content.
- **JWTs and refresh tokens** must only ever live in memory or localStorage on the
  client, and in the JWT-signed body in transit. Never write them to logs.
- **`.env` files are git-ignored.** Verify with `git check-ignore backend/.env` — it
  should return the path.
- **Report a suspected security issue** to Khaled directly by email — see the
  contact link in `.github/ISSUE_TEMPLATE/config.yml`. Do NOT open a public issue for
  it.
- **Impersonation** is an admin capability. Use it only when it's the fastest way to
  reproduce a student's problem, and mention on the audit trail why you did it.

---

## 15. AI Prompt Changes

Prompts that affect what students see — the internship coach, project coach, LinkedIn
coach, GitHub coach, proofread, draft-summary — are treated as **product-critical
copy**, not code.

When changing a prompt:

- **Preserve the honesty rules.** Every coach prompt embeds a rule against inventing
  facts (`_HONESTY_RULES` in `career_pack_service.py`, plus per-prompt constraints).
  Never remove those.
- **Test both directions.** Feed the prompt (a) rich input to make sure it produces
  good output, and (b) intentionally sparse input to make sure the vague-path or
  refusal still fires.
- **Diff the JSON response schema.** If you change the output shape, update the DTO,
  the frontend consumer, and the tests in one PR.
- **Attach 2-3 real transformations** to the PR description: what the student typed
  and what the LLM produced. Reviewers can eyeball for hallucination.
- **Never remove the deterministic fallback** in the renderer. If the LLM is
  unavailable, students still get a usable CV.
- Prompts are in these files — flag any PR touching them for Khaled:
  - `backend/app/application/services/student_coach_service.py`
  - `backend/app/application/services/career_pack_service.py`

---

## 16. CV Template / Export Changes

Templates and exports are the single point of failure for the whole product. Treat
them accordingly.

**PDF templates** live at `backend/app/application/templates/student_cv/*.html`. There
are five: `classic`, `modern`, `minimal`, `academic`, `creative`.

**DOCX renderer** lives at `backend/app/application/services/student_cv_docx_renderer.py`.

**Every template / export change PR must:**

- Preserve the empty-section skip behaviour. A partial-profile student should never
  see a blank "Skills" heading.
- Render every populated section. Add a section to `_SECTION_ORDER` in **both** the
  HTML renderer and the DOCX renderer if you're adding a new entry kind.
- Test all five PDF templates. Download each and open it.
- Test the DOCX in **both** Microsoft Word and Google Docs. They handle Word features
  differently — a change that renders in one can break in the other.
- Confirm the mobile CV preview still fits its viewport.
- If adding a new entry kind: migration (Postgres enum) + Python tuple + DTO literal +
  renderer section order + PDF templates + DOCX renderer, all in the same PR. Same
  three-line lockstep pattern we've followed for `internship`, `career_pack.*`, and
  `cv.docx`.
- Preserve ATS-friendliness for DOCX: no text boxes, no floating shapes, no image-based
  text, single-column body (Modern's sidebar table is the one intentional exception).

Reviewers must see side-by-side screenshots of the affected template before/after.

---

## 17. Email Template Changes

Templates live at `backend/app/infrastructure/email/templates/*.html` + `.txt`.

**Every email template change PR must:**

- Render locally through `render(template_name, ctx)` and confirm zero unresolved
  `{placeholder}` literals — placeholder leaks in production are a common bug.
- Include screenshots of the rendered HTML in both Gmail and (if reachable) Outlook.
- Use Outlook VML fallbacks for any CTA button (`<!--[if mso]><v:roundrect ...`).
- Not use inline HTML comments that contain `{placeholder}` values — Gmail's parser
  strips them inconsistently and the URL leaks as visible text (we've been bitten by
  this).
- Add the new template ID to `EMAIL_TEMPLATES` in
  `backend/app/application/email_templates.py`.
- Preserve the plain-text `.txt` fallback so mail clients that block HTML still show
  the message.

For new templates, include the design mockup in the issue and reference it from the PR.

---

## 18. Getting Help

- **Open a `question` issue** for anything that might help someone else later. Most
  answers belong here so they become searchable history.
- **Comment on the relevant PR or issue** if you're blocked on something in flight —
  it pings the author and anyone watching.
- **For production-affecting emergencies** (site down, data loss risk), open a
  `hotfix/` branch immediately (see `README_DEVELOPMENT_PROCESS.md`) and mention
  `@KSMozn` on the PR so the notification hits him fast.

Welcome aboard. Small PRs, honest tests, screenshots — that's the whole culture.
