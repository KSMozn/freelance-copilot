# CLAUDE.md — AI Development Guide for the Careero Monorepo

This is the **repo-root** guide: the map plus the rules that apply everywhere.
Each area has its own mandatory guide — **read the one for the area you are
touching before changing anything there**:

| Area | Guide | Stack |
| --- | --- | --- |
| `backend/` | `backend/CLAUDE.md` | FastAPI · SQLAlchemy 2 async · Alembic · Python 3.13 · uv |
| `frontend/` | `frontend/CLAUDE.md` | Vite 6 · React 18 · TS · TanStack Query · Zustand · Base UI |
| `docs/` | `docs/CLAUDE.md` | Architecture/ERD/roadmap docs — must track code |
| `marketing/` | — | Zero-dependency static-site generator; deployed separately via its own `cloudbuild.yaml` |

## What this product is

**Careero** (student CV-builder wizard, `app.careero.app`) + **PersonaArmory
Admin** (ops console, `admin.careero.app`) + a static marketing site
(`careero.app`). One frontend bundle serves both app surfaces, selected at
runtime by hostname / sticky `?surface=` param.

**The professional/career-OS surface is DORMANT, not dead**: backend
endpoints remain live and tested; the frontend code is quarantined in
`frontend/src/features/professional/` with routes deliberately unregistered
and ESLint-enforced isolation. Reviving or deleting it is a product decision,
never a refactor side-effect.

## Repo-wide hard rules

- **Never push. Commit only when the developer explicitly asks.**
- **Never add `Co-authored-by`, AI attribution, or agent attribution lines**
  for Claude, Copilot, or any other agent unless the developer explicitly asks.
- **Package managers**: `backend/` = uv (`uv.lock`); `frontend/` and
  `marketing/` = npm (`package-lock.json`). Never introduce a `yarn.lock`.
- **API contracts are bilateral**: any change to a backend route/DTO must land
  with the matching frontend change (and vice versa). The live surface is
  `/auth`, `/students`, `/career-pack`, `/admin`, `/admin/auth`.
- **Never touch the dormant professional surface** (backend endpoints or
  `features/professional/`) without an explicit request.
- **Migrations are append-only** — never edit or delete an existing Alembic
  revision; history is linear with a single head.
- **CODEOWNERS is load-bearing** (`.github/CODEOWNERS`): if you move a file
  listed there, update its path in the same change.
- Secrets never enter the repo: config flows through `.env` (see
  `.env.example` at root + `backend/.env.example` — keep both in sync with
  `backend/app/core/config.py`).
- Dev conveniences: `make up` (full stack), `make create-admin`,
  `make backend-test`, `make lint`. Dev email is captured, never sent:
  OTP codes + reset links land in `backend/var/dev-emails.jsonl` (mock
  provider), readable via `GET /api/v1/dev/emails` (development+mock only)
  and surfaced directly in the auth screens' dev-mode helper boxes.

## Deployment shape (context, not instructions)

GCP project `freelance-copilot-841590`, Cloud Run services
`freelance-copilot-{backend,frontend}` + `marketing`, region `europe-west1`.
Release flow and environment details: `README_DEVELOPMENT_PROCESS.md`.
Contribution flow, branch naming, review gates: `CONTRIBUTING.md`.
