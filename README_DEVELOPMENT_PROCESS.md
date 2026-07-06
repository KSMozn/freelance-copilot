# Careero — Development Process

This document is the "how we work" reference for the Careero team. Read `CONTRIBUTING.md`
first for the mechanics (branches, PRs, testing); this file explains the shape of the
process — roles, environments, releases, cadence.

---

## 1. Overall Development Workflow

We use **GitHub Flow**. Short-lived branches off `main`, small PRs, squash merges,
delete the branch. That's the whole model.

```
                            main (always production-ready)
                              |
   +----------------+---------+----------+----------------+
   |                |                    |                |
 feature/           fix/               chore/          hotfix/
 short-lived        short-lived        short-lived     urgent
   |                |                    |                |
   +--- PR + review + tests -------------+                |
                              |                           |
                              v                           |
                          squash merge                    |
                              |                           |
                              +--- prod deploy <----------+
```

- **No Git Flow, no develop branch, no release branches.** Overkill for a small team.
- **Feature flags** are used when a change needs to land unfinished; hidden behind an
  env var or a build-time toggle. Preferred to long-lived feature branches.
- **Migrations always ship in the same PR as the code that needs them.**
- **Docs live next to code.** New env var → update `backend/.env.example` in the same
  PR. New endpoint → include a curl example in the PR body.

---

## 2. Roles and Responsibilities

| Role | Who | Owns |
|---|---|---|
| **Maintainer** | Khaled | Final approval on user-facing product, CV builder, templates, exports, AI prompts, email templates, auth, env vars, production deploys. Merges. |
| **Team contributor** | Invited collaborators | Opens branches, ships PRs, reviews others' PRs, runs local tests. May approve small fixes but not sensitive-area changes. |
| **Reviewer of the week** | Rotates | First responder on new PRs (target: first review within 24h business days). |
| **On-call for prod** | Khaled | Deploys, hotfixes, rollbacks. |

Anyone can propose a change. Only the maintainer merges to `main`.

---

## 3. Environments

Careero runs in **two environments** — production and local. There is **no shared staging
environment**. In practice we've found that a running local stack (docker compose) plus
strong PR reviews and a smoke checklist catches the same regressions a staging
environment would, without the infra cost.

### 3.1 Local

- `docker compose up -d` in the repo root.
- Frontend at `http://localhost:5173`, backend at `http://localhost:8000`.
- Postgres, backend, and frontend containers.
- Mock email provider (writes to `backend/var/dev-emails.jsonl` — never actually sends).
- OpenAI-compatible API talks to the real Groq if configured, otherwise mock.

This is where **every PR is validated** before requesting review. The full pre-merge
checklist runs here.

### 3.2 Production

- **URLs:**
  - Student: `https://app.careero.app` (Careero brand) + `https://app.personaarmory.com`
    (PersonaArmory brand). Same Cloud Run service, different domain mapping.
  - Admin: `https://admin.careero.app` + `https://admin.personaarmory.com`.
  - Backend: `https://api.careero.app` + `https://api.personaarmory.com`.
- **Cloud Run** services: `freelance-copilot-backend`, `freelance-copilot-frontend`.
- **Cloud SQL** Postgres 15: `freelance-copilot-db`.
- **GCS bucket** for uploads: `freelance-copilot-841590-uploads`.
- **Secrets** in GCP Secret Manager.
- **Region:** `europe-west1`.

Production is deployed **only by Khaled**, only from `main`. Never from a branch.

### 3.3 Emulating Staging Locally

If you need to test something that's already merged to `main` but not yet deployed:

```bash
git checkout main
git pull
docker compose down
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

That gives you a local instance running the exact code that's queued for the next
deploy. Good enough for "does this compose with the last three merges" checks.

---

## 4. How Work Moves From Idea to Production

```
IDEA
  |
  v
ISSUE (with acceptance criteria + labels)
  |
  v
BRANCH (feature/short-name off main)
  |
  v
LOCAL WORK
  |  - implement
  |  - self-test the checklist in CONTRIBUTING §9
  |  - commit small, buildable steps
  v
PR (small, well-described, screenshots for UI)
  |
  v
REVIEW  --- comments? --> address --- rebase if main moved --- re-request review
  |
  v
APPROVE (+1 review minimum, Khaled for sensitive areas)
  |
  v
CI GREEN + all comments resolved + branch up to date
  |
  v
SQUASH MERGE to main
  |
  v
BRANCH DELETED
  |
  v
DEPLOY (by Khaled, from main) --- see §5
  |
  v
SMOKE TEST in prod (release checklist)
  |
  v
ISSUE CLOSED, PR CLOSED, done.
```

Anything that doesn't reach "done" in ~5 business days should get chunked smaller. If
the PR is stalled, comment on the issue and hand it back to the queue.

---

## 5. Release Process

We release continuously — every merged PR that touches user-facing code gets deployed
the same day or the next. Larger releases (a new wizard step, a new export format) get
a scheduled window and a smoke pass.

### 5.1 The Deploy Sequence

Every prod deploy runs this exact order. Skipping a step has burned us before.

```bash
# 0. Pre-flight
git checkout main && git pull
git log --oneline -5    # confirm you're at the intended commit

# 1. Build backend image (contains migrations + code)
cd backend
gcloud builds submit \
  --tag europe-west1-docker.pkg.dev/freelance-copilot-841590/freelance-copilot/backend:<short-slug>-<sha> \
  --project=freelance-copilot-841590 \
  --account=easydynamicstmiller@gmail.com \
  --machine-type=e2-highcpu-8 .

# 2. Build frontend image in parallel
cd ../frontend
gcloud builds submit --config=cloudbuild.yaml \
  --project=freelance-copilot-841590 \
  --account=easydynamicstmiller@gmail.com .

# 3. Point migrate job at new image + run migrations (order matters: BEFORE backend swap)
gcloud run jobs update freelance-copilot-migrate \
  --image=<the-new-backend-tag> \
  --region=europe-west1 --project=freelance-copilot-841590
gcloud run jobs execute freelance-copilot-migrate \
  --region=europe-west1 --project=freelance-copilot-841590 --wait

# 4. Roll backend
gcloud run services update freelance-copilot-backend \
  --region=europe-west1 --image=<the-new-backend-tag> \
  --project=freelance-copilot-841590

# 5. Roll frontend
gcloud run services update freelance-copilot-frontend \
  --region=europe-west1 \
  --image=europe-west1-docker.pkg.dev/freelance-copilot-841590/freelance-copilot/frontend:latest \
  --project=freelance-copilot-841590

# 6. Smoke test
# Run through .github/RELEASE_CHECKLIST.md against https://app.careero.app.
```

### 5.2 What "Ready to Release" Means

- All merged PRs since the last release show green in CI.
- No unresolved `blocker` issues open.
- Release checklist has been walked on a local instance running `main`.
- Rollback anchors noted (previous backend and frontend revision IDs).

### 5.3 Rollback

If the smoke test fails or an alert fires:

```bash
gcloud run services update-traffic freelance-copilot-backend \
  --to-revisions=<previous-revision>=100 \
  --region=europe-west1 --project=freelance-copilot-841590
gcloud run services update-traffic freelance-copilot-frontend \
  --to-revisions=<previous-revision>=100 \
  --region=europe-west1 --project=freelance-copilot-841590
```

Migration rollbacks are rare — we prefer forward-fixing. Postgres enum values are
additive-only anyway.

---

## 6. Hotfix Process

For urgent production bugs — site down, data loss risk, security issue:

1. **Branch off `main`**: `hotfix/<short-description>`.
2. **Fix the smallest possible thing** to stop the bleeding. Don't refactor.
3. **Open a PR.** Yes, hotfixes still require a PR — they still get review, they
   still squash-merge.
4. **Khaled approves and merges.** He can also self-review in a genuine emergency but
   at least one other pair of eyes is strongly preferred.
5. **Deploy immediately** using the sequence above.
6. **Open a follow-up issue** for any cleanup or root-cause work that got deferred.
   The hotfix branch contains ONLY the urgent fix — related tidiness goes into a
   normal PR the next day.

Hotfixes bypass the "wait for the next release window" cadence but not the
"PR + review + green CI" gate.

---

## 7. Weekly Development Rhythm

We're a small team; the rhythm is intentionally light.

| Day | Cadence |
|---|---|
| Monday | 15-minute sync: what shipped last week, what's in flight, blockers. |
| Every day | Async standup as a comment on the current sprint's tracking issue — one line, no ceremony. |
| Wednesday | "Review afternoon" — reviewers clear the PR queue. |
| Friday | Merge freeze after 3pm local. Only hotfixes merge over the weekend. |
| Monthly | Retrospective: what worked, what didn't, one process tweak. |

- **Working async** is the default. Meetings only when async is genuinely worse.
- **Issue triage** happens in the Monday sync — labels, priorities, assignees.
- **Nothing merges on Friday afternoons** unless it's a hotfix. Prod on the weekend
  with nobody watching is how bad Mondays start.

---

## 8. Quality Gates

Each gate exists because we hit a bug that got past the previous gate.

| Gate | What it checks | Failure mode it catches |
|---|---|---|
| **Local run** | The dev's own docker stack. | Obvious build breakage. |
| **CI** | Type check, build, unit tests. | Missed imports, type drift. |
| **Peer review** | Correctness, blast radius, matches issue. | Logic errors, hidden coupling. |
| **UI review** | Screenshots + local walk-through. | Empty states, mobile, "I forgot to test that path". |
| **Release checklist** | End-to-end journey in prod. | Prod-only bugs (env vars, secrets, custom domains). |
| **Post-deploy smoke** | Real students in the affected screens. | The bug the checklist didn't cover. |

If a gate misses a bug, the retrospective adds a line to that gate's checklist so it
catches the next one.

---

## 9. How to Avoid Breaking the CV Generation Journey

The CV generation journey is `register → wizard → preview → download`. It's the
product. When it's broken, we have no product.

**Rules that keep it working:**

- **Every renderer change requires a full journey walk.** Register a new student on
  your local, fill the wizard, download PDF and DOCX, open both.
- **Never remove the deterministic fallback** from the CV renderer. If the LLM is
  unavailable, the CV still renders.
- **Empty sections must not render as empty headings.** The `build_context()` in
  `student_cv_renderer.py` filters them out; don't route around it.
- **`_SECTION_ORDER` is the single source of truth** for section ordering. Change it
  in exactly one place, in the same PR that adds the new kind.
- **Migrations and Python enum tuples ship together.** Every new `student_entry_kind`
  or `usage_event_kind` value requires: Postgres `ALTER TYPE` migration + Python
  tuple + DTO literal, all in the same commit. We've been bitten twice by drift.
- **DOCX and PDF are tested separately.** They share the context builder but the
  render paths are independent — a bug in DOCX doesn't show in PDF and vice versa.
- **The `?step=<slug>` deep-link routing** is used by email CTAs. Any change to the
  wizard's step slugs is a **breaking change** for existing email templates. Update
  the templates or add aliases in the same PR.
- **Photo transform lives in Pillow**, not the frontend. Any change to
  `_make_circular_photo` requires testing across landscape, portrait, and square
  aspect ratios (there's a regression test for this — keep it green).
- **Admin funnel denominator = number of wizard steps.** Bump it in three places when
  a new step is added: `WIZARD_STEPS` tuple in `admin_service.py`, `AdminUsers.tsx`
  denominator, `AdminUserDetail.tsx` denominator.

**When you're unsure whether a change touches the journey**, treat it as if it does.
Cheap paranoia beats expensive rollbacks.

---

## 10. Anti-Patterns We've Retired

Things we tried, that didn't work, that we're not doing again:

- **Long-lived feature branches** — always end in a painful rebase. Use feature
  flags.
- **Merging without a screenshot on UI PRs** — silent regressions on mobile.
- **Sending real users to a "test" prod slug** — confuses them, creates fake events.
- **Manual JWT hacks in the browser** to bypass admin login — use the admin surface
  properly (`?surface=admin` locally, `admin.` subdomain in prod).
- **Skipping the migrate job "because nothing schema-changed"** — enum values are
  schema.
- **Running `alembic downgrade` in prod** — Postgres enum values can't be removed
  without rebuilding the type. Forward-fix instead.

---

## 11. Onboarding a New Contributor

Rough day-1 to day-3 for a new team member:

- **Day 1:** Read `CONTRIBUTING.md`, this file, and the top-level `README.md` (if any).
  Set up local. Sign into a local admin. Walk the CV creation journey as a student.
- **Day 2:** Pick a `good-first-issue`. Open the branch. Ship a PR. Get review.
- **Day 3:** Merge the first PR. Attend the Monday sync.

If any step takes longer than a day, we have a documentation bug — open an issue
against `CONTRIBUTING.md` or this file so it gets fixed for the next contributor.
