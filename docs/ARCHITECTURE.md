# Architecture

## Principles

- **Clean Architecture** — dependencies point inward. The Domain layer knows
  nothing about FastAPI, SQLAlchemy, OpenAI, or Claude.
- **SOLID** — small focused classes, interfaces (`Protocol`s) at every layer
  boundary, dependency inversion for every external concern.
- **Async-first** — every IO boundary is async (DB, HTTP, future LLM calls).
- **Repository pattern** — persistence is hidden behind repository protocols.
- **Service layer** — application logic lives in services that orchestrate
  repositories and external services.
- **DTOs (Pydantic v2)** — schemas at the API boundary and between layers.
- **Dependency Injection** — wired via FastAPI's `Depends` and a small
  `app/core/deps.py` container.

## Layers

```
┌──────────────────────────────────────────────────────────────────┐
│  api/            FastAPI routers, request/response schemas        │  ← outer
│    v1/endpoints/   auth.py · jobs.py · health.py · ...            │
├──────────────────────────────────────────────────────────────────┤
│  application/   Services, DTOs, use-case orchestration            │
│    services/      auth_service.py · job_service.py · ...          │
│    dto/           job_dto.py · auth_dto.py · ...                  │
├──────────────────────────────────────────────────────────────────┤
│  domain/        Entities, value objects, repository protocols     │
│    entities/      user.py · job.py · ...                          │
│    repositories/  job_repository.py (Protocol) · ...              │
│    exceptions.py                                                  │
├──────────────────────────────────────────────────────────────────┤
│  infrastructure/  SQLAlchemy models, repo impls, AI providers    │  ← inner
│    db/models/      user.py · job.py · ...                         │
│    db/repositories/   sqlalchemy_job_repository.py · ...          │
│    ai/             (Phase 2+) openai_provider.py · claude_...     │
├──────────────────────────────────────────────────────────────────┤
│  core/          Cross-cutting: config, security, db session, DI   │
└──────────────────────────────────────────────────────────────────┘
```

Direction of dependencies: `api → application → domain ← infrastructure`.
The Domain layer is leaf — it imports nothing from the others.

## Module wiring

`app/core/deps.py` exposes `get_*_service` callables for FastAPI. Each one
requests an `AsyncSession` and constructs a repository implementation, which
is injected into the service. Routers depend only on services.

```python
# app/api/v1/endpoints/jobs.py
@router.post("", response_model=JobRead)
async def create_job(
    payload: JobCreate,
    service: JobService = Depends(get_job_service),
    user: User = Depends(get_current_user),
) -> JobRead: ...
```

Swapping the persistence backend, adding a fake repo for tests, or swapping
OpenAI for Claude requires no changes outside `infrastructure/` + `core/deps.py`.

## Authentication

JWT (HS256 in dev, RS256-ready in `core/security.py`). Two parallel sign-in
paths share the same token model:

**Password (legacy):**
- `POST /api/v1/auth/register` — create user with email + password, return access + refresh tokens.
- `POST /api/v1/auth/login` — verify credentials, return tokens.

**Email OTP (Phase A — primary path going forward):**
- `POST /api/v1/auth/request-code` — issue a 6-digit code, email it via the configured provider. Rate-limited (3 / 15 min / email).
- `POST /api/v1/auth/verify-code` — verify the code. If the email isn't yet registered, the account is created on the fly (no password). Marks `email_verified_at` and returns tokens.

**Shared:**
- `POST /api/v1/auth/refresh` — rotate access token from refresh token.
- `GET  /api/v1/auth/me` — current user (includes `email_verified_at`, `last_login_at`).

Passwords (when used) are hashed with `bcrypt` via `passlib`. OTP codes are
also bcrypt-hashed before storage — the server never persists plaintext codes.
Tokens carry `sub` (user id), `type` (`access`/`refresh`), `exp`, `iat`.

`EmailOtpService` (`application/services/email_otp_service.py`) handles issue +
verify with rate-limit, attempt cap, and expiry. It depends on `EmailProvider`
(see below) for delivery.

### Email provider abstraction (Phase A)

Mirrors the `AIProvider` pattern:

```python
class EmailProvider(Protocol):
    name: str
    async def send(self, message: EmailMessage) -> EmailSendResult: ...
```

Implementations in `infrastructure/email/`:
- `MockEmailProvider` (dev default) — writes outgoing messages to `var/dev-emails.jsonl` and logs the OTP code. Zero network.
- `ResendEmailProvider` — calls the Resend transactional email API. Recommended prod default.

Templates live next to the providers under `infrastructure/email/templates/`
(`otp_login.html` + `otp_login.txt`) and render via `template_renderer.render()`
— plain `str.format_map` for now, easy to swap for Jinja2 if templates grow.

Selection via `EMAIL_PROVIDER=mock|resend` in `app/core/config.py`, factory in
`app/infrastructure/email/factory.py`.

## Professional Knowledge Graph (Phase B)

The graph holds the *facts* of a user's professional identity in a normalized
shape that personas (Phase C) project lenses over. Tables and entities:

- `skill_catalog` — global normalized skill master list (slug + name +
  category + aliases). Seeded with ~120 common technologies / practices /
  soft skills; free-form user-added skills land here too.
- `user_skills` — the per-user "pot": one row per (user, skill) with
  proficiency, evidence count, and a `sources` JSONB that tracks which
  repos / resumes / portfolios / CV uploads / LinkedIn snapshots / manual
  edits / AI suggestions contributed.
- `experiences` (+ `experience_skills`, `experience_achievements`) — work
  history items populated by CV / LinkedIn ingestion (Phase D) or manual
  entry. Empty after Phase B; backfill is Phase D territory.
- `projects` (+ `project_skills`, `project_achievements`) — unified
  surface that subsumes portfolios and scanned repositories. Phase B
  backfill creates one project per existing portfolio (`origin=portfolio`)
  and one per scanned repo (`origin=repo`).

Services in `app/application/services/`:

- **`SkillCatalogService`** (`skill_catalog_service.py`) — the single
  funnel: slugify → exact-slug lookup → alias-match → fuzzy trigram
  (`pg_trgm` similarity ≥ 0.85) → create-new. Every ingest seam calls this
  so the pot stays deduplicated.
- **`KnowledgeGraphService`** (`knowledge_graph_service.py`) — high-level
  orchestrator. Phase B exposes `add_skill_evidence` (used by future
  ingest paths) and `list_user_skills`. Phase D extends with
  `ingest_from_cv`, `ingest_from_linkedin`, `add_certificate`.
- **`PersonaProfileResolver`** (`persona_profile_resolver.py`) — produces
  the legacy `FreelancerProfile` dataclass shape from per-user
  `user_skills` + `skill_catalog`, so the scoring engine code stays
  untouched but every user now drives scoring from *their own* graph.
  Falls back to `DEFAULT_FREELANCER_PROFILE` for users with an empty pot.

The Phase B backfill migration (`0019_phase_b_backfill`) walks every existing
user's resumes / portfolios / repositories, normalizes the raw skill strings
through the catalog (auto-creating unknown rows), aggregates evidence into
`user_skills` with a `sources` provenance map, and creates one `projects`
row per portfolio + per repository. Idempotent: safe to re-run.

## Personas as lenses (Phase C)

A persona is a *lens* over the user's knowledge graph — not a copy of it.
The same user_skills / experiences / projects feed every persona; what
changes is how they're weighted, ordered, framed, and surfaced.

Tables:
- `persona_archetypes` — system-seeded templates (11 today: IC, Senior
  Engineer, Tech Lead, Staff, Principal, Eng Manager, Director, AI Engineer,
  Solutions Architect, Consultant, Freelancer). Immutable from user CRUD.
- `personas` — per-user instances of an archetype. Carry overrides
  (`weights`, `skill_category_weights`, `proposal_tone`,
  `strategic_priorities`) and pinning arrays
  (`pinned_experience_ids`, `pinned_project_ids`, `pinned_skill_ids`).
  Exactly one `is_default` per user, enforced by a partial unique index.

Services:
- **`PersonaService`** (`persona_service.py`) — CRUD + lifecycle. Notable
  methods: `instantiate_from_archetype` (auto-uniques the name across the
  user's personas), `ensure_primary` (idempotent default-persona creation,
  called from `AuthService.verify_otp` so every new account lands on a
  working dashboard), `delete` (refuses to delete the last persona,
  auto-promotes another to default if a default is deleted).
- **`PersonaProfileResolver`** (extended in Phase C) — now produces a
  `FreelancerProfile` whose `weights`, `strategic_priorities`, and pinned
  skills reflect the active persona. Merge precedence: persona override →
  archetype default → static fallback. The scoring engine code is
  unchanged.

Wiring:
- `get_scoring_service` and `get_portfolio_matching_service` in
  `core/deps.py` are now async — they await
  `PersonaProfileResolver.load_for_user(user_id)` and pass the resulting
  per-user `FreelancerProfile` into the scoring/matching services. Every
  authenticated request scores against the active persona's profile, with
  zero changes to the scoring or matching code itself.
- `AuthService` accepts an optional `PersonaService` and calls
  `ensure_primary` on every successful `verify_otp`. New OTP users get a
  default `Primary` persona (instantiated from the `senior_engineer`
  archetype) before they hit the dashboard.

API surface (`/api/v1/personas`):
- `GET /personas/archetypes` — list the 11 seeded archetypes.
- `GET /personas` — list the current user's personas.
- `GET /personas/current` — the user's default persona (idempotent — creates
  Primary if absent).
- `POST /personas` — create from an archetype slug.
- `GET /personas/{id}` / `PATCH /personas/{id}` — read / partial update
  (whitelisted fields only).
- `POST /personas/{id}/set-default` — promote a persona to default
  (uses the partial unique index to enforce one-default-per-user).
- `DELETE /personas/{id}` — refuses to delete the user's only persona;
  auto-promotes another to default if the deleted one was default.

Frontend:
- `PersonaSwitcher` in the topbar — dropdown with the active persona,
  switch list, "+ New persona", "Manage personas." Switching calls
  `/personas/{id}/set-default` so the choice persists across reloads.
- `/personas` index page — card grid with default badge, "Make default,"
  "Delete."
- `/personas/new` — 2-step wizard: archetype gallery, then name +
  target role. Submits to `POST /personas`.
- `auth.ts` (Zustand) gains `activePersonaId` — mirrored from the
  server-resolved default so other components can read it synchronously.

## AI Provider Abstraction

```python
class AIProvider(Protocol):
    async def complete_json(self, *, system_prompt, user_prompt) -> AIRawResponse: ...
    async def complete_json_with_image(
        self, *, system_prompt, user_prompt, image_bytes, image_mime_type
    ) -> AIRawResponse: ...
```

Implementations in `infrastructure/ai/`: `OpenAIProvider`, `ClaudeProvider`,
`MockAIProvider`. Selection is configuration-driven
(`AI_PROVIDER=openai|claude|mock`). All prompts return strict JSON, validated
in the application layer against task-specific Pydantic schemas — no
free-text parsing.

The two methods share most of the HTTP logic. The image-enabled method
serializes the image into the provider's native content-block format
(`image_url` for OpenAI, `image / base64` for Anthropic) and is used by the
Phase-7+ "import a job from a screenshot" flow.

## Embeddings & semantic search (Phase 3)

`pgvector` is enabled in the database. The `embeddings` table stores
`(owner_type, owner_id, model, vector)` rows so the same infra embeds jobs,
portfolio projects, and — in later phases — resumes and proposals. The `model`
column carries a provider-qualified id (e.g. `mock:mock-hash-1536`,
`openai:text-embedding-3-small`) so two providers never trample each other.

An `EmbeddingProvider` protocol (`domain/providers/embedding_provider.py`) is
the outbound port; `MockEmbeddingProvider` (feature-hashing, unit length) and
`OpenAIEmbeddingProvider` (text-embedding-3-small, normalized on the way out)
are the implementations.

`PortfolioMatchingService` (application layer) ranks portfolios by the hybrid
score `0.60·semantic + 0.25·skill_overlap + 0.10·domain_overlap + 0.05·strategic`.
Per-user portfolio sets are small, so cosine is computed in Python over a
single `embeddings` query; swap in a pgvector ANN query when that changes
without touching the scoring rules.

## Resume library (Phase 4)

The same embedding pipeline is reused for resumes. `ResumeService` is a sibling
of `PortfolioService` — CRUD + embed-on-write — and writes rows into the same
polymorphic `embeddings` table with `owner_type='resume'`.

`ResumeRecommendationService` ranks the user's resume profiles for an analyzed
job using a hybrid score with weights tuned for resume↔job fit:
`0.55·semantic + 0.30·skill_overlap + 0.10·domain_overlap + 0.05·seniority`.
Skill overlap is asymmetric and weighted — a primary-skills hit contributes
1.0, a secondary-skills hit contributes 0.5, of the per-job-skill point.
Seniority alignment walks an ordered scale (`junior < mid < senior < lead <
staff < principal`) and rewards exact + adjacent matches.

The two services intentionally stay separate rather than collapsing into a
generic "match-via-embeddings" helper: they share infrastructure but differ in
weights, explanation fields, and the templates that build their text
representations.

## Proposal generation + review (Phase 5)

The AIProvider port carries a single method `complete_json(system_prompt,
user_prompt) -> AIRawResponse`. Task semantics live in the prompt, not the
port — the analyzer (Phase 2) and the proposal generator (Phase 5) share it,
and the MockAIProvider routes by inspecting the user prompt for task markers.

`ProposalGenerationService` orchestrates the full pipeline:

1. Load the job; require its analysis + opportunity score (Phase 2).
2. Recompute fresh portfolio matches (Phase 3) and resume recommendations
   (Phase 4). Cached embeddings make this cheap.
3. Build a compact prompt context — truncated job description, top-N
   skills/risks/deliverables, top score dimensions, top 2 portfolio matches,
   top 1 resume — so prompts stay within budget regardless of input size.
4. Call `complete_json`; validate the response against `ProposalDraftSchema`.
5. Run the deterministic `ProposalReviewService` against the draft.
6. Persist body + structured fields + quality data into `proposals`.

`ProposalReviewService` is pure and stateless. It scores eight dimensions —
specificity, relevance, portfolio evidence, clarity, brevity, non-generic
wording, risk awareness, call to action — and returns a 0–100 total plus
explicit warnings per failing dimension. The banned-phrase list is shared
with the prompt module so prompt and review can never drift.

Editing a proposal goes through the same generation service: `update` writes
the new body; `re_review` re-runs the deterministic check against the edited
text. Quality data is always against the current body.

## Application tracker (Phase 6)

`ApplicationStateMachine` is a pure domain function. It maps each status to
its set of allowed next statuses; `validate_transition` raises an
`InvalidTransitionError` for self-loops and illegal moves. Terminal states
(`rejected`, `withdrawn`, `completed`) have an empty allowed-next set. The
frontend imports the same table at compile time and renders only the
transitions the backend will accept.

`ApplicationService` orchestrates the full create-from-proposal pipeline:
load the proposal (its `job_id`, `resume_id`, and `portfolio_ids` are
authoritative) → enforce the one-active-app-per-job invariant → call the
matching + recommendation services to capture the talking points / positioning
advice the user actually saw → call
`build_snapshot` to assemble an immutable JSONB blob → write the row + the
initial history entry.

The snapshot lives in `applications.snapshot` and is captured by value: the
job title, budget, opportunity score breakdown, proposal body + quality,
resume positioning, and portfolio talking points are all copied at submission
time. Phase 8's learning loop (planned) depends on this — editing or deleting
the source rows after the fact must not retroactively change history.

Status transitions go through `update_status`. The service captures
`from_status` by value before delegating to the repository, since some repos
(notably the in-memory fakes) mutate the entity in place. Each transition
emits a row into `application_history` with an optional note, and sets the
per-status timestamp the first time we enter a state.

## Analytics (Phase 7)

Read-only. The whole pipeline lives in three small modules:

- `domain/analytics/definitions.py` — pure predicates: `is_interviewed`,
  `is_won`, `is_lost`, etc. Every other module imports from here so the
  semantics are defined exactly once.
- `application/services/analytics_extraction.py` — pure functions that pull
  the analytics-relevant facts out of an application snapshot: score /
  quality buckets, budget bucket, known-technology matcher, known-domain
  matcher. Order of preference: structured snapshot fields first, body-text
  fallback last. Pattern matching is regex with word-boundary
  lookbehind/lookahead so `.NET` and `C++` work and `API` doesn't match
  inside "rapidly".
- `application/services/analytics_service.py` — `AnalyticsService`
  composes 11 sections (overview, funnel, outcome rates, score
  effectiveness, proposal quality effectiveness, technologies, domains,
  budgets, revenue, time-to-status, recent activity). Pure Python over the
  per-user application set; no materialized views per the spec. The set is
  small enough that a single round-trip is cheap.

The endpoint is `GET /api/v1/analytics/dashboard?from_date=&to_date=`.
Dates filter `applications.created_at` inclusively.

Analytics never joins back to mutable `jobs`/`proposals`/`resumes` rows —
the Phase-6 snapshot is the source of truth. That's the same guarantee
Phase 8's learning loop will lean on.

## Testing strategy

- **Unit** — services and domain logic with in-memory fake repositories.
- **Integration** — pytest with a disposable Postgres (Docker) verifying
  repositories and end-to-end API flows.
- **E2E** — Playwright drives the frontend against a seeded backend.

## Configuration

All settings come from environment variables, parsed by `pydantic-settings`
in `app/core/config.py`. No hard-coded secrets.

## Database

PostgreSQL 16 with the `vector` extension. See [`ERD.md`](ERD.md) for the
schema. Migrations are managed by Alembic; the Phase-1 baseline migration
creates every table that downstream phases will use.
