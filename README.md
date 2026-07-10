# Careero — AI Career Platform for Students

**Careero** (a **PersonaArmory** product) helps university students build a
polished, recruiter-ready CV through a guided 13-step wizard with inline AI
coaching — then export it as PDF or DOCX and level up their LinkedIn/GitHub
presence with a generated Career Starter Pack.

One repository, three deployed surfaces, one frontend bundle:

| Surface | Host | What it is |
| --- | --- | --- |
| **Student app** | `app.careero.app` | The CV-builder wizard (OTP email sign-in) |
| **Admin console** | `admin.careero.app` | PersonaArmory ops: users, funnel, feedback, emails, CV templates, LLM spend |
| **Marketing site** | `careero.app` | Static pre-rendered site (`marketing/`, deployed separately) |

> **History:** the repo began as an "Upwork Intelligence Platform" for
> freelancers. That professional/career-OS surface still exists — backend
> endpoints live, frontend quarantined in
> `frontend/src/features/professional/` with its routes deliberately
> unregistered — but the shipping product is Careero. Do not delete or
> re-mount the dormant surface casually; see the CLAUDE.md guides.

## Repository layout

```
.
├── backend/     FastAPI · SQLAlchemy 2 (async) · Alembic (44 migrations) · PostgreSQL + pgvector
│                Clean Architecture: api → application → domain ← infrastructure
├── frontend/    Vite 6 · React 18 · TypeScript · Tailwind v3 · Base UI + CVA
│                Feature-driven: app/ + features/{auth,student-wizard,admin,professional} + shared/
│                TanStack Query (server state) · Zustand (client state) · Storybook
├── marketing/   Zero-dependency static-site generator for careero.app (own Dockerfile + cloudbuild)
├── docs/        Architecture, ERD, roadmap, LLM-visibility playbook
├── .github/     CI (ruff + mypy + pytest, lint + typecheck + build, Playwright E2E), CODEOWNERS, issue/PR templates
├── docker-compose.yml · Makefile · CONTRIBUTING.md · README_DEVELOPMENT_PROCESS.md
└── CLAUDE.md    AI-agent guides (root, backend/, frontend/, docs/)
```

## Quickstart (Docker)

```bash
cp .env.example .env
make up            # postgres + backend (auto-migrates) + frontend
make create-admin email=you@example.com password=change-me
```

- Student app: <http://localhost:5173>
- Admin console: <http://localhost:5173/login?surface=admin>
- Backend API: <http://localhost:8000> (OpenAPI docs at `/docs` outside production)

### Email on localhost — nothing reaches a real inbox (by design)

The dev stack runs `EMAIL_PROVIDER=mock`: every email (OTP codes,
password-reset links) is **captured locally** in
`backend/var/dev-emails.jsonl` instead of being sent. If you're watching your
Gmail inbox, nothing will ever arrive — that's not a bug.

You don't have to open that file. In development the auth screens show a
"Development mode — emails are captured locally" box:

- **OTP steps** display the latest captured code with a **Use code** button.
- **Forgot password** displays an **Open reset link** button after the
  request.

Both are backed by `GET /api/v1/dev/emails`, a mailbox endpoint that only
exists when `ENVIRONMENT=development` **and** `EMAIL_PROVIDER=mock` (it 404s
everywhere else, and staging/production refuse to boot on the mock provider
at all). Production sends real email via Resend with the exact same auth
flow — only the delivery adapter differs.

## Local development (without Docker)

```bash
make backend-dev    # uvicorn --reload (needs Python 3.13 + `uv sync` in backend/)
make frontend-dev   # vite dev server on :5173
make lint           # ruff (backend) + eslint/tsc (frontend)
make backend-test   # pytest inside the backend container (363 unit tests, no DB needed)
```

Frontend extras: `npm run storybook` (shared/ui component browser),
`npm run build-storybook`, `npm run format`. Husky runs lint-staged on every
commit (hooks live in `frontend/.husky/`).

## Providers (all mockable, selected via env)

| Concern | Options | Notes |
| --- | --- | --- |
| LLM | `AI_PROVIDER=mock\|openai\|claude` | `mock` is the offline default; Groq works through `OPENAI_BASE_URL` (OpenAI-compatible). |
| Embeddings | `EMBEDDING_PROVIDER=mock\|openai` | Used by the dormant professional surface. |
| Email | `EMAIL_PROVIDER=mock\|resend` | `mock` writes to `backend/var/dev-emails.jsonl` (OTP codes + password-reset links) and powers the dev mailbox endpoint; `resend` sends real mail and is required in staging/production (the app refuses to boot there on `mock`). Same auth flow either way — only the delivery adapter changes. |
| Uploads | `BLOB_STORE=local\|gcs` | Local dir or GCS bucket. |

See `.env.example` (root, full stack) and `backend/.env.example` for the
complete variable reference.

## Going deeper

- **`README_DEVELOPMENT_PROCESS.md`** — environments, Cloud Run deploys, release flow.
- **`CONTRIBUTING.md`** — branch naming, PR flow, review gates (CODEOWNERS).
- **`docs/ARCHITECTURE.md`** — backend layering + subsystem walkthroughs.
- **`docs/ERD.md`** — database schema per migration.
- **`docs/ROADMAP.md`** — phase history (professional era + Careero era).
- **`CLAUDE.md` / `backend/CLAUDE.md` / `frontend/CLAUDE.md` / `docs/CLAUDE.md`** —
  mandatory rules for AI-assisted development in each area.
