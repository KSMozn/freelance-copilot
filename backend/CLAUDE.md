# CLAUDE.md — AI Development Guide for the Careero Backend

## Project Overview

FastAPI backend serving **three API surfaces** from one app (`/api/v1`):

- **Live — Careero student product**: `/auth` (OTP + password), `/students`
  (profile, entries, coaching, CV preview/PDF/DOCX, feedback/survey),
  `/students/career-pack`.
- **Live — PersonaArmory admin**: `/admin/auth`, `/admin` (users, funnel,
  emails, CV templates, feedback, LLM spend, impersonation, daily-report task).
- **Dormant — professional career-OS**: `/jobs`, `/proposals`, `/portfolio`,
  `/resumes`, `/repositories`, `/applications`, `/analytics`, `/personas`,
  `/outputs`, `/match-reports`, ingestion, tracker, career-fitness. Fully
  implemented and unit-tested; its frontend is quarantined. **Do not modify or
  remove these endpoints without an explicit request.**

> **Package manager / runtime:** Python **3.13**, `uv` (`pyproject.toml` +
> `uv.lock`). No requirements.txt. Tests need no database.

---

## Tech Stack

- **Framework**: FastAPI ≥0.115 + Uvicorn
- **DB**: PostgreSQL 16 + pgvector, SQLAlchemy 2 async (`asyncpg`), Alembic (44 linear migrations, single head)
- **Auth**: PyJWT (HS256), passlib bcrypt; refresh-token rotation with family revocation
- **Validation**: Pydantic v2 + pydantic-settings (`app/core/config.py` is the single settings source)
- **AI**: provider ports — `AI_PROVIDER=mock|openai|claude` (Groq via `OPENAI_BASE_URL`), `EMBEDDING_PROVIDER=mock|openai`; **mock is the default and must keep working offline**
- **Email**: `EMAIL_PROVIDER=mock|resend` — mock writes `var/dev-emails.jsonl`; non-mock enforced in staging/production
- **PDF/DOCX**: WeasyPrint (native libs in Dockerfile) + python-docx; Jinja2 CV templates in `app/application/templates/student_cv/`
- **Lint/format**: ruff (configured in pyproject: line 100, py313, E/F/I/B/UP/N/ASYNC/RUF)
- **Types**: mypy `strict=true`, **gated in CI** — exits 0 via the explicit ratchet baseline (see Testing)
- **Tests**: pytest + pytest-asyncio (`asyncio_mode=auto`), unit-only

---

## Architecture — Clean Architecture DAG

```
api/v1/endpoints/     thin routers; DI via app/core/deps.py
  ↓
application/          services (orchestration) + dto/ (Pydantic) + templates/
  ↓
domain/               entities, repository Protocols, provider ports, pure logic
  ↑
infrastructure/       SQLAlchemy models/repos, ai/, email/, github/, http/, storage/
core/                 config, database, security, deps (DI), rate_limit
```

Rules:
- `domain/` imports nothing from other layers (verified clean — keep it so).
- `api/` never touches the DB or infra directly — endpoints depend on services from `core/deps.py`.
- **New application services must depend on domain repository interfaces**, wired in `core/deps.py` — never import `app.infrastructure.db.models.*` or concrete `sqlalchemy_*_repository` classes directly.

### ⚠️ Known layering debt (documented, deliberate — do NOT extend)

The live Careero services took shortcuts the dormant code did not: these import
ORM models or concrete repos directly — `admin_service`, `daily_report_service`,
`feedback_service`, `student_profile_service`, `student_coach_service`,
`student_cv_renderer`, `student_cv_docx_renderer`, `career_pack_service`,
`cv_template_service`, `usage_event_service` (ORM models);
`admin_auth_service`, `refresh_token_manager` (concrete repos). Tolerated as-is;
**new code must not copy this pattern**, and fixing it is a deliberate future
refactor, not a drive-by.

---

## Auth model — two identity spaces

- **Users/students** → `get_current_user` / `CurrentUser` (`core/deps.py`).
  Every `/students`, `/career-pack`, and professional route is user-gated.
- **Admins** → `get_current_admin` / `CurrentAdmin`; admin JWTs carry
  `pt=admin`. The two gates mutually reject each other's tokens; admin
  identities live in `admin_users`, never in `users`.
- **Impersonation**: `/admin/users/{id}/impersonate` mints a short-lived USER
  token pair (`IMPERSONATION_TOKEN_EXPIRE_MINUTES`) handed to the SPA via URL
  fragment — never weaken this contract.
- **Machine endpoint**: `POST /admin/tasks/daily-report` uses the
  `X-Task-Secret` header (constant-time compare, fail-closed outside dev).
- **Rate limiting**: in-process sliding window (`core/rate_limit.py`) on auth
  surfaces only (login/OTP/refresh, per-IP + per-account). Deliberately no
  Redis — documented trade-off; don't add distributed limiting casually.
- Security headers + CORS validation live in `main.py`/`config.py`; API docs
  are disabled in production.

---

## Database & migrations

- Alembic history is **linear, single-head, append-only** (`0001` … `0044`).
  Never edit an existing revision. New revision: `make revision m="..."`.
- Models live in `infrastructure/db/models/`; keep them in sync with
  migrations (autogenerate, then hand-review).
- Live-surface tables: `users`, `admin_users`, `student_profiles`,
  `student_profile_entries`, `cv_templates`, `email_otp_codes`,
  `usage_events`, `feedback_entries`, `career_packs`, `refresh_tokens`,
  `password_reset_tokens`, `uploaded_files`. Everything else belongs to the
  dormant surface — leave it.

---

## Testing

- `make backend-test` (pytest in the container) or `pytest` locally via uv.
  **Unit tests only**: in-memory fakes (`tests/factories.py`) + `TestClient`
  with `app.dependency_overrides` — no Postgres, no network, mock providers.
- Follow the existing patterns (`tests/test_api_portfolio.py` is canonical for
  API tests; `tests/test_refresh_rotation.py` for auth flows).
- **Every new/changed live endpoint needs an API test.** Coverage is
  historically inverted (dormant surface well-tested, live surface thin) —
  `tests/test_api_students.py` / `test_api_admin.py` / `test_api_auth_live.py`
  are the live-surface suite; extend them, don't regress them.
- CI (`.github/workflows/ci.yml`) gates: `ruff check .` + `mypy app` +
  `pytest -q`, installed with `uv sync --frozen` so the lockfile governs CI.
  mypy strict **exits 0 and is gated**: the remaining 2026-07 debt
  (**98 errors in 27 of 262 files**, dormant surface + CV renderers + infra
  adapters only) is held in an explicit `[[tool.mypy.overrides]]` ratchet
  baseline in `pyproject.toml`. All security/live-surface modules (`core/*`,
  auth/admin/students/career-pack endpoints and their services) are
  strict-clean. Shrink the baseline as modules get cleaned — **never add an
  entry**, and never introduce `Any` in new code.

---

## Conventions

- DTOs in `application/dto/*.py` (Pydantic v2); endpoints return DTOs, never
  ORM rows. Errors are `HTTPException(detail=str)` → `{"detail": "..."}` —
  keep `detail` a string (the SPA renders it directly).
- Route changes are **bilateral contracts** — update the matching frontend
  `<feature>Api.ts` in the same change and vice versa.
- Prompts/AI calls go through the provider ports with strict JSON + Pydantic
  validation; the mock provider must recognize every new prompt marker so the
  offline pipeline keeps working.
- CLI scripts live in `app/scripts/` (`seed` = dormant demo data;
  `create_admin` = live admin bootstrap, env-var driven, idempotent).
- No `print()` in app code (scripts only), no TODOs left behind — file an
  issue or fix it.

---

## Hard Rules

- **Never push. Commit only when the developer explicitly asks.**
- **Never add AI/agent attribution lines to commits.**
- Never edit or delete an existing Alembic migration.
- Never change a live API contract without the matching frontend change.
- Never touch the dormant professional endpoints without an explicit request.
- New services depend on domain interfaces — never ORM models/concrete repos.
- Keep `backend/.env.example` and the root `.env.example` in sync with
  `config.py` whenever settings change.
- The mock providers (AI/email/embeddings) must always keep the full product
  usable offline — never make a real key mandatory for dev or tests.
