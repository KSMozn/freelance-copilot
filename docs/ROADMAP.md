# Implementation Roadmap

Phase 1 lays a complete foundation that downstream phases extend without
schema rewrites. Each subsequent phase is independently shippable.

## Phase 1 — Foundation ✅

- Clean Architecture skeleton (api · application · domain · infrastructure)
- Full PostgreSQL schema (every table the platform will ever need)
- JWT auth: register · login · refresh · me
- Jobs CRUD: create · list · get · update · delete · archive
- Frontend shell: login/register, dashboard, jobs list, job detail, job create
- Docker Compose (postgres+pgvector, backend, frontend)
- CI placeholder, Makefile, env templates

---

## Phase 2 — AI Job Analyzer + Opportunity Scoring ✅

**Goal:** structured extraction + deterministic 0–100 opportunity score on every
imported job. Phase 2 also folds in what was originally Phase 4 (scoring) so
recommendations are usable today.

- `domain/providers/ai_provider.py` — `AIProvider` protocol.
- `infrastructure/ai/` — `MockAIProvider` (default, no network),
  `OpenAIProvider`, `ClaudeProvider`. All return JSON validated against a
  Pydantic schema; free-text parsing is forbidden.
- Prompt module under
  [`application/services/prompts.py`](../backend/app/application/services/prompts.py)
  tagged with `PROMPT_VERSION` so analyses are traceable.
- `JobAnalysisService` orchestrates: load job → call provider → validate →
  upsert `job_analyses` → run `ScoringService` → upsert `opportunity_scores` →
  return both.
- `ScoringService` is pure: eight dimension functions sum to 100
  (technical fit 25, domain fit 10, proposal count 20, budget 10, client
  quality 10, effort 10, risk 10, strategic value 5), driven by a
  `FreelancerProfile`. Recommendation thresholds: ≥80 Strong Apply, ≥65 Apply,
  ≥50 Maybe, else Skip.
- Migration `0002_phase2_analysis_scoring` adds structured analyzer fields and
  creates `opportunity_scores`.
- API:
  - `POST /api/v1/jobs/{id}/analyze`
  - `POST /api/v1/jobs/{id}/reanalyze`
  - `GET  /api/v1/jobs/{id}/analysis`
- UI: "Analyze job" / "Re-analyze" on Job Detail; ScoreCard, ScoreBreakdown
  bars, summary, extracted skills/technologies, risks, red/green flags,
  questions-to-ask-the-client.

**Exit:** new jobs are analyzed + scored on demand; `mock` provider keeps tests
and local dev free of network/cost; `score_breakdown` sums to the headline
`score` invariant is unit-tested.

---

## Phase 3 — Portfolio Knowledge Base + Semantic Matching ✅

- Migration `0003_phase3_portfolio` reshapes the Phase-1 placeholder
  `portfolios` table to the Phase-3 contract (title, short/long descriptions,
  role, business_domain, technologies, skills, features, outcomes).
- `EmbeddingProvider` protocol + `MockEmbeddingProvider` (deterministic
  feature-hashing, 1536-d unit vectors) + `OpenAIEmbeddingProvider`
  (text-embedding-3-small). Selected via `EMBEDDING_PROVIDER=mock|openai`.
- `PortfolioService` issues an embedding on every create/update and stores it
  in the polymorphic `embeddings` table keyed by `(owner_type, owner_id,
  model_id)`. Lazy `ensure_embedding` re-embeds portfolios when the provider
  changes.
- `PortfolioMatchingService` hybrid score:
  `0.60·semantic + 0.25·skill_overlap + 0.10·domain_overlap + 0.05·strategic`.
  Cosine is computed in Python over the small per-user portfolio set; ANN
  upgrade is a no-op when scale changes.
- Endpoints:
  - `POST /api/v1/portfolio`, `GET /api/v1/portfolio`,
    `GET /api/v1/portfolio/{id}`, `PUT /api/v1/portfolio/{id}`,
    `DELETE /api/v1/portfolio/{id}`
  - `POST /api/v1/jobs/{id}/match-portfolio`,
    `GET /api/v1/jobs/{id}/portfolio-matches`
- UI: full Portfolio list + form pages, **Match portfolio** card on Job Detail
  showing per-component scores, reasons, relevant skills/domains, and
  suggested talking points.

**Exit:** with the demo seed (FastAPI/RAG job + 4 portfolios), the AI
Document Q&A portfolio scores ~71% match vs ~31% for an unrelated WordPress
project. Score components are unit-tested; provider switching is one env
flip.

---

## Phase 4 — Resume Library + Resume Recommendation ✅

- Migration `0004_phase4_resume` reshapes the Phase-1 placeholder `resumes`
  table to the Phase-4 contract (title, target_role, summary, seniority_level,
  primary_skills, secondary_skills, industries, domains, achievements,
  project_highlights, keywords, notes).
- `ResumeService`: CRUD + embed-on-write, reusing the Phase-3
  `EmbeddingProvider` abstraction and the polymorphic `embeddings` table with
  `owner_type='resume'`. Same lazy `ensure_embedding` for provider switches.
- `ResumeRecommendationService` hybrid score:
  `0.55·semantic + 0.30·skill_overlap + 0.10·domain_overlap + 0.05·seniority`.
  Skill overlap is weighted (primary = 1.0, secondary = 0.5). Missing /
  weak skills are explicitly surfaced from the job's required + preferred +
  technologies list.
- Endpoints:
  - `POST/GET/PUT/DELETE /api/v1/resumes[/{id}]`
  - `POST /api/v1/jobs/{id}/recommend-resume`,
    `GET /api/v1/jobs/{id}/resume-recommendations`
- UI: Resumes list + create/edit/delete pages and a **Recommend resume**
  card on Job Detail (top recommendation + alternatives, fit reasons,
  missing/weak skills, positioning suggestions).

**Exit:** the demo seed (FastAPI/RAG job + 5 resumes) ranks the AI/LLM resume
top at ~72%, with missing/weak skills called out per profile and seniority
mismatches flagged in the fit reasons.

---

## Phase 4.5 — Scoring v2 *(deferred)*

What was originally Phase 4 (per-user FreelancerProfile + embedding-based
`TechnicalFitScorer`) is now deferred until the Proposal Generator (Phase 5)
lands — that phase shares prompt templating and is the natural home for
per-user customization.

---

## Phase 5 — Proposal Generator + Quality Review ✅

- Migration `0005_phase5_proposal` reshapes the Phase-1 placeholder
  `proposals` table to the Phase-5 contract (title, short_body, structured
  questions/milestones/delivery_approach/risk_notes, portfolio_ids,
  resume_id FK, quality_score + breakdown + warnings, prompt_version,
  raw_response).
- `AIProvider.analyze_job` → `AIProvider.complete_json`. The MockAIProvider
  routes by a `--- PROPOSAL ASSIGNMENT ---` marker so analyzer and proposal
  calls stay in one port.
- `proposal_prompts.py` carries `PROMPT_VERSION` and `BANNED_PHRASES`. The
  same banned list drives the review's `non_generic_wording` dimension.
- Prompt-context builder caps job description at ~2.5k chars (word
  boundary), top 8 required skills, top 3 risks/hidden requirements, top 4
  deliverables, top-3 score dimensions, top 2 portfolio matches, top 1
  resume recommendation.
- `ProposalGenerationService`: load job → require analysis + score → fetch
  fresh matches/recommendations → build context → `complete_json` →
  Pydantic-validate → review → persist. Returns the persisted DTO.
- `ProposalReviewService` is pure: 8 dimensions summing to 100
  (specificity 20, relevance 20, portfolio_evidence 15, clarity 15,
  brevity 10, non_generic_wording 10, risk_awareness 5, call_to_action 5).
  Each dimension emits warnings; banned-phrase hits dock the score and emit
  explicit warnings.
- Endpoints: generate, list, latest, get, update, delete, re-review.
- UI: Proposal card on Job Detail — editable headline / body / short body,
  copy buttons, milestones, questions, delivery approach, risk notes, the
  8-dimension breakdown, and warnings. Edit + re-run review updates in place.

**Exit:** the demo job + 4 portfolios + 5 resumes produces an 82/100
proposal that passes all banned-phrase checks; editing the body to contain
"I am excited to apply" + "I am a perfect fit" drops the score and surfaces
explicit warnings, both in unit tests and via the API.

---

## Phase 6 — Application Tracker + Outcome Snapshots ✅

- Migration `0006_phase6_application` extends `applications` (per-status
  timestamps, contract_amount, client_response, rejection_reason,
  portfolio_ids, snapshot JSONB), adds `draft` + `offer` to the
  `application_status` enum, and adds a `user_id` to `application_history`.
- `ApplicationStateMachine` (domain layer) encodes valid transitions:
  draft → applied → viewed → interview → offer → won → completed, with
  rejected/withdrawn reachable from any non-terminal state. Self-transitions
  and transitions out of terminal states are rejected.
- `ApplicationService.create_from_proposal` builds an immutable JSONB
  snapshot at submission time: job, opportunity score, proposal body +
  quality, recommended resume + its positioning advice, top portfolio
  matches with talking points. Editing the source rows later can never
  rewrite history.
- One active application per job; previous applications in
  rejected/withdrawn/completed unblock a fresh one.
- Status transitions emit `application_history` rows with optional note
  and always set the per-status timestamp the first time we enter a state.
- Endpoints:
  - `POST /api/v1/applications/from-proposal/{proposal_id}`
  - `GET /api/v1/applications`, `GET /api/v1/applications/{id}`
  - `PATCH /api/v1/applications/{id}/status`
  - `PATCH /api/v1/applications/{id}` (details: contract_amount, etc.)
  - `GET /api/v1/applications/{id}/history`
  - `DELETE /api/v1/applications/{id}`
- UI: `/applications` Kanban grouped by status; per-application detail page
  shows the snapshot, status timeline, transition buttons (derived from the
  shared state-machine table), and editable details. Job Detail's proposal
  card flips its bottom action between **Mark as Applied** and an
  **Applied · {status}** link.
- Seed now generates a demo application end-to-end (analyze → propose →
  apply), idempotent.

**Exit:** end-to-end mock-provider run produces an `applied` application
with a complete snapshot (proposal body 82/100, opportunity score 85,
matched portfolio with talking points, resume with positioning) and walks
through applied → viewed → interview → offer → won → completed with the
correct timestamps + history rows.

---

## Phase 7 — Analytics Dashboard ✅

- Outcome definitions centralized in
  `app/domain/analytics/definitions.py` — `is_interviewed` is inclusive
  through won/completed (and respects an explicit `interview_at` timestamp);
  `is_lost` covers rejected + withdrawn.
- Pure extraction + bucketing helpers in
  `analytics_extraction.py`: score buckets, quality buckets, budget bucket
  (parsed from the snapshot's `job.budget` string), word-boundary tech
  matcher that handles `.NET` / `C++`, and a domain matcher with structured
  + body-parse fallback.
- `AnalyticsService` composes 11 dashboard sections in pure Python.
  Aggregates over `applications.snapshot` + status + timestamps +
  `application_history`. No materialized views. Optional `from_date` /
  `to_date` filter on `applications.created_at`.
- Endpoint: `GET /api/v1/analytics/dashboard?from_date=&to_date=`.
- Frontend dashboard at `/analytics` with Recharts; date-range picker;
  empty-state handling per section.
- Seed creates 10 varied demo applications (across statuses, scores,
  domains, budgets, contract amounts, back-dated across months).

**Exit:** the demo dataset produces win-rate breakdowns by score bucket
(80–100 bucket shows the highest win rate), domain (AI SaaS wins more than
FinTech), and technology (FastAPI/Python lead). Funnel rates fall from
viewed (~100%) down to win (~40%), and time-to-status surfaces realistic
hour/day deltas across the pipeline.

---

---

# Career OS rebuild (Phases A–J)

These phases evolve the app from a single-user proposal generator into the
Engineering Career OS described in `/Users/khaledsamir/.claude/plans/cached-waddling-puzzle.md`.
Each phase is independently shippable. **Web MVP = phases A–G**; phases H–J are
roadmap.

## Phase A — Email-OTP signup + verification ✅

**Goal:** replace password-only signup with email-token sign-in so users can
get into the app in 90 seconds without remembering a password, and so the
platform owns a verified-email contact path for future features (digests,
notifications).

- Migration `0015_phase_a_email_otp` adds:
  - `email_otp_codes` table — bcrypt-hashed 6-digit codes, 10-min TTL,
    purpose enum (`login`/`register`/`email_change`), attempt cap, IP/UA
    forensics columns, indexes on `(email, purpose, consumed_at)` and
    `expires_at`.
  - `users.email_verified_at` + `users.last_login_at`.
  - `users.password_hash` made NULLABLE (OTP-only accounts have no password).
- New domain port `EmailProvider` (`domain/providers/email_provider.py`),
  mirroring the `AIProvider` pattern.
- Concrete providers under `infrastructure/email/`:
  - `MockEmailProvider` — writes outgoing mail to `var/dev-emails.jsonl` and
    logs the OTP code. Zero network. Dev default.
  - `ResendEmailProvider` — Resend API client. Recommended prod default.
- `EmailOtpService` (`application/services/email_otp_service.py`) — issue +
  verify with rate-limit (3 issues / 15 min / email), bcrypt-hashed code
  storage, attempt cap, expiry.
- Templates: `infrastructure/email/templates/otp_login.{html,txt}` rendered
  via `template_renderer.render()` (plain `str.format_map` — swap for Jinja2
  if templates grow).
- API:
  - `POST /api/v1/auth/request-code` — issue OTP, rate-limited.
  - `POST /api/v1/auth/verify-code` — verify code; auto-creates the user
    on first verify so signup and sign-in are a single flow.
  - `GET /api/v1/auth/me` now returns `email_verified_at` + `last_login_at`.
  - Existing `/register`, `/login`, `/refresh` unchanged — password path
    kept as a secondary option.
- Frontend:
  - `Login.tsx` rewritten as a 2-step OTP flow (email → code) with a
    "use a password instead" fallback.
  - New `/onboarding` page — the **"one thing"** post-signup screen.
    Three cards: Upload CV (placeholder until Phase D), Connect GitHub
    (functional today), Skip. Users land here only on their first session
    (server flags this via `last_login_at == null` in the auth response).
- Settings additions: `EMAIL_PROVIDER`, `RESEND_API_KEY`,
  `EMAIL_FROM_ADDRESS`, `EMAIL_FROM_NAME`, `APP_NAME`, `OTP_EXPIRES_MINUTES`,
  `OTP_MAX_ATTEMPTS`, `OTP_RATE_LIMIT_PER_15MIN`, `FRONTEND_BASE_URL`.
  Wired through `docker-compose.yml` and `.env.example`.

**Exit:** `curl /auth/request-code` writes a code to `var/dev-emails.jsonl`;
`curl /auth/verify-code` returns a JWT pair for a freshly-created or existing
user; the user lands on `/onboarding` for their first session and on `/` for
subsequent sessions. Password login keeps working for legacy accounts.

---

## Phase B — Knowledge graph foundations ✅

**Goal:** move `FreelancerProfile` from a static singleton to a per-user
projection over a normalized skill catalog + skill pot. Backend reshape
only; no UI changes. Existing flows keep working unchanged.

- Migration `0016_phase_b_catalog_and_pot` — `skill_catalog` (slug UNIQUE,
  name, category enum, aliases JSONB, GIN + trigram indexes via `pg_trgm`)
  and `user_skills` (the per-user "pot" — proficiency, sources JSONB,
  evidence_count, pinned, UNIQUE(user_id, skill_id)).
- Migration `0017_phase_b_graph_core` — `experiences` (+ `experience_skills`,
  `experience_achievements`) and `projects` (+ `project_skills`,
  `project_achievements`). Projects subsume portfolios + scanned repositories
  via `origin` enum and `repo_id` / `portfolio_id` links.
- Migration `0018_phase_b_seed_catalog` — seeds ~120 common skills
  (Python / TypeScript / FastAPI / React / PostgreSQL / AWS / GraphQL / RAG /
  Microservices / Mentoring / FinTech / …). Idempotent.
- Migration `0019_phase_b_backfill` — for every user, walks resumes,
  portfolios, repositories; normalizes each raw skill string via slug →
  alias → fuzzy trigram (auto-creates unknown rows with
  `is_system_seeded=false`); aggregates into `user_skills` with `sources`
  provenance map; creates one `projects` row per portfolio
  (`origin=portfolio`) and per repository (`origin=repo`). Idempotent.
- Services:
  - `SkillCatalogService` (`app/application/services/skill_catalog_service.py`)
    — single normalize funnel used by every ingest seam.
  - `KnowledgeGraphService` (`knowledge_graph_service.py`) — high-level
    orchestrator. Phase B exposes `add_skill_evidence` + `list_user_skills`;
    Phase D extends with CV / LinkedIn ingestion.
  - `PersonaProfileResolver` (`persona_profile_resolver.py`) — produces the
    legacy `FreelancerProfile` shape from `user_skills + skill_catalog`,
    falling back to `DEFAULT_FREELANCER_PROFILE` for empty pots. **This is
    the seam that lets Phase C plug personas in without scoring-engine
    code changes.**
- New SQLAlchemy models + domain entities + repositories for
  `skill_catalog`, `user_skills`, `experiences`, `projects` and their
  join tables.

**Exit:** the demo user's pot has 146 user_skills rows aggregated from
4 portfolios + 7 repositories + their resumes; `PersonaProfileResolver`
returns a per-user `FreelancerProfile` whose `strong_skills` reflect the
actual pot (PostgreSQL, Python, FastAPI, RAG, OpenAI, …) and whose
`version` is `user:<uuid>` rather than `default-v1`. Existing test suite
remains green (197/197 of the meaningful tests). No user-facing changes —
scoring code still reads the static default; Phase C wires the resolver
in for real once personas exist.

---

## Phase C — Personas as lenses ✅

**Goal:** instantiate personas as user-facing lenses over the knowledge
graph and wire the scoring engine to read through `PersonaProfileResolver`.
Biggest user-value unlock — a single user can now apply to one job as
"Tech Lead" and another as "AI Engineer" and the system reflects both
framings end-to-end.

- Migration `0020_phase_c_personas` — `persona_archetypes` (system-seeded
  templates) + `personas` (per-user instances) tables. Personas table
  carries overrides (weights, skill_category_weights, proposal_tone,
  strategic_priorities) and pinning arrays (pinned_experience_ids /
  pinned_project_ids / pinned_skill_ids). Partial unique index enforces
  exactly one default persona per user.
- Migration `0021_phase_c_seed_archetypes` — seeds 11 archetypes:
  Individual Contributor, Senior Engineer, Tech Lead, Staff Engineer,
  Principal Engineer, Engineering Manager, Director of Engineering,
  AI Engineer, Solutions Architect, Consultant, Freelancer. Each ships
  scoring weights (summing to 100), category emphasis (summing to 1.0),
  proposal tone, target roles, and seniority band. Idempotent upsert.
- Migration `0022_phase_c_backfill_primary` — creates a `Primary` persona
  (from the `senior_engineer` archetype, `is_default=true`) for every
  existing user. Idempotent.
- Services:
  - `PersonaService` — CRUD + lifecycle: `instantiate_from_archetype`
    (auto-uniques names), `ensure_primary` (idempotent default-persona
    creation called from auth), `set_default` (with single-default
    invariant), `delete` (refuses last persona; auto-promotes a new
    default when needed).
  - `PersonaProfileResolver` (extended) — now merges persona overrides
    over archetype defaults over the static fallback to produce the
    `FreelancerProfile` shape. Pinned skills bypass the proficiency
    threshold and always appear in `strong_skills`.
  - `AuthService` gains an optional `PersonaService` and calls
    `ensure_primary` after every successful `verify_otp` so brand-new
    OTP signups land with a working default persona.
- DI rewiring (`core/deps.py`):
  - `get_scoring_service` and `get_portfolio_matching_service` are now
    async — they await `PersonaProfileResolver.load_for_user(user.id)`
    and pass the per-user `FreelancerProfile` into the underlying
    services. Scoring engine + matching code stay untouched.
- API (`/api/v1/personas`):
  - `GET /archetypes`, `GET /`, `GET /current`, `POST /`, `GET /{id}`,
    `PATCH /{id}`, `POST /{id}/set-default`, `DELETE /{id}`.
- Frontend:
  - `PersonaSwitcher` in the topbar — dropdown with active persona,
    switch list, "+ New persona," "Manage personas." Switching persists
    server-side via `set-default`.
  - `/personas` index — card grid with default badge, "Make default,"
    "Delete."
  - `/personas/new` — 2-step wizard: archetype gallery (11 cards) →
    name + target role.
  - Sidebar entry "Personas."
  - `auth.ts` (Zustand) gains `activePersonaId`, mirrored from the
    server-resolved default.

**Exit:** the demo user has the auto-created Primary persona;
`PersonaProfileResolver.load_for_user(demo_id)` returns
`version=persona:<uuid>` with archetype-derived weights + the per-user
strong_skills already wired in Phase B. New OTP signups get a Primary
persona automatically. Existing tests stay green (197/197). Scoring on
any job now flows through the active persona's weights without any
scoring-engine code change.

---

## Phase D — Source ingestion (CV + LinkedIn + certificates + content) ✅

**Goal:** the knowledge graph grows beyond the Phase B portfolios/repos
backfill via four ingest paths. The "one thing" onboarding card stops
being a placeholder.

- Migration `0023_phase_d_ingestion` adds `uploaded_files` (generic blob
  registry with UNIQUE per-user sha dedup), `cv_uploads`,
  `linkedin_snapshots`, `certificates`, `content_items`.
- Added backend deps `pdfminer.six` (PDF) + `python-docx` (DOCX).
- Pipeline (`CvIngestService`):
  upload bytes → sha256 dedup → text extraction
  (pdfminer.six / python-docx / paste passthrough) → INSERT
  `parse_status='parsing'` → LLM-structure via `structure_cv()`
  (Pydantic-validated JSON shape) → `KnowledgeGraphService.ingest_from_cv`
  (auto-creates skills, upserts user_skills with `cv_upload_ids`
  provenance, INSERTs experiences with dedup on lower(company)+role+start)
  → UPDATE `parse_status='parsed'` with the structured JSON +
  flattened skill list. On any failure, the row flips to `failed` with a
  human-readable `parse_error` so the UI can show what went wrong.
- Services:
  - `text_extraction.py` — pure PDF/DOCX/text extractor. Raises
    `TextExtractionError` for image-only PDFs / unsupported types.
  - `cv_structuring.py` — Pydantic schema + system prompt + LLM
    structuring call. Truncates input to ~12 K chars. Mock provider
    recognizes `CV_INGEST_MARKER` and returns a heuristic deterministic
    structured payload (companies + roles via regex; skills via known-set
    matcher) so dev / offline runs exercise the full pipeline.
  - `CvIngestService`, `LinkedInIngestService` — orchestrators. Persist
    blobs under `var/uploads/<sha256>` (bind-mount volume → survives
    container restarts).
  - `KnowledgeGraphService.ingest_from_cv()` — extended to write
    experiences + experience_skills + experience_achievements via the
    new `ExperienceRepository`. Backwards compatible: callers that pass
    no experience repo fall back to skills-only ingest.
  - `SkillCatalogService` (Phase B) is the single funnel for skill
    normalization — every CV skill string flows through slug → alias →
    fuzzy trigram before landing in the catalog + pot.
- API (`/api/v1`):
  - `GET /cv-uploads`, `POST /cv-uploads` (multipart), `POST /cv-uploads/paste`.
  - `GET /linkedin`, `POST /linkedin/import` (multipart PDF).
  - `GET /certificates`, `POST /`, `PATCH /{id}`, `DELETE /{id}`.
  - `GET /content-items`, `POST /`, `PATCH /{id}`, `DELETE /{id}`.
- Frontend:
  - `/sources` page — unified surface for all four ingest paths.
    Card-per-source layout. CVs offer paste-or-upload. Status badges
    (pending / parsing / parsed / failed) per upload row.
  - Onboarding "Upload CV" card now routes to `/sources` (was a stub).
  - Sidebar entry "Sources" beside Personas.

**Exit:** pasted-CV smoke test on the demo user produces 2 experiences +
10 user_skills rows with `sources.cv_upload_ids` populated. Backend boots
clean through 0023; existing test suite stays green (197/197 of the
meaningful tests). Files persist across container restarts via the
backend bind-mount.

---

## Phase E — Persona-aware match report + gap recommendations ✅

**Goal:** every `(job, persona)` pair gets a persisted, scored, gap-fixed
match analysis. Job detail page gains the new Match Report card.

- Migration `0024_phase_e_match_reports` — `match_reports` table keyed by
  `(job_id, persona_id)` UNIQUE. Captures all existing dimensions
  (technical / architecture / domain) plus the Phase E additions
  (`leadership_fit`, `soft_skills_fit` — both nullable, "not applicable"
  is a first-class state), `missing_critical_skills` (with importance +
  status), `missing_recommendations`, `rationale`, `profile_version`.
- `MatchReportService` — orchestrator. Composes `JobConfidenceService`
  for the base dimensions, `SkillEvidenceService` to attach importance
  to missing skills, `leadership_signals` (Phase E) for the new
  dimensions, `PersonaProfileResolver` for the profile stamp, and
  `GapRecommendationService` for the recs. UPSERTs by `(job, persona)`;
  caching is implicit unless caller passes `force=true`.
- `leadership_signals.py` — pure detectors + scorer. Returns NULL when
  the job carries no leadership / soft signals so IC roles aren't
  scored against irrelevant criteria.
- `GapRecommendationService` — turns missing skills into structured
  recommendations of 5 kinds:
  `project_to_build`, `certification`, `learning_resource`,
  `github_enhancement`, `experience_to_emphasize`. Phase E ships
  deterministic canned rules for ~15 high-frequency skills (Kafka,
  Kubernetes, Terraform, RAG, AWS / GCP / Azure cert paths, …) +
  generic fallback for anything else. Phase G hooks market signals in.
- Overall recomposition: when leadership / soft are scored, the headline
  weights shift so leadership-heavy roles can lift Eng Manager scores
  without inflating IC scores.
- API:
  - `POST /jobs/{id}/match-report?persona_id=…&force=…` — build-or-get.
  - `GET /jobs/{id}/match-reports` — list all persona-keyed reports for
    a job (used in Phase F's parallel-analyses tab strip).
- Frontend:
  - `MatchReportCard` on Job Detail — overall + dimensions + persona
    chip + "Re-run" button + structured recommendation list (per-kind
    icon, effort estimate, priority).
  - Persona-aware: reads `activePersonaId` from the Zustand store; the
    report re-fetches when the user switches personas via the topbar.

**Exit:** smoke test on demo data produces a persisted match report
(`profile_version=persona:<uuid>`) with 6 missing skills → 6 prioritized
recommendations (Azure cert, learning resources for niche skills,
fallback templates). Leadership_fit + soft_skills_fit are both scored
because the test job carries leadership signals. Existing test suite
stays green (197/197).

---

## Phase F — Multi-format outputs + citations *(next)*

`OutputGenerationService` unifies generation; `CitationService` attaches
evidence chips. New output kinds: cover letter, recruiter reply, LinkedIn
message, consulting proposal, screening answer, tailored resume. Existing
proposals migrate as `kind=upwork_proposal`. Every claim cites a graph
node (experience / project / repo / cert / content).

---

## Phase 8 — Learning Loop

- Periodic job: for each won/lost outcome, write back features into a
  training set and re-fit the dimension weights in the scoring config.
- A/B holdout to verify lifts before adopting new weights.

---

## Phase 9 — Hardening

- Rate-limit & quota on LLM calls per user.
- Cost dashboard.
- Audit log of every AI call (prompt hash, tokens, latency, cost).
- Playwright E2E coverage for golden paths.
- GitHub Actions: lint, type-check, test, build, push images.
