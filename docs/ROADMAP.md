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

## Phase B — Knowledge graph foundations *(planned)*

Move `FreelancerProfile` from a static singleton to per-user graph projection.
Adds `skill_catalog`, `user_skills` (the global "pot"), `experiences`,
`projects`, and backfills the legacy `skills` / `portfolios` / `repositories`
data into the new shape. No UI changes yet.

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
