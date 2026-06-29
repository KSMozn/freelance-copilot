# Upwork Intelligence Platform

AI-powered decision support for freelancers. Helps you decide whether to apply for a
job, generates personalized proposals, tracks applications, and learns from outcomes.

> This is **not** an automation or scraping tool. The platform never logs into
> Upwork, never submits proposals, and never performs any action against Upwork's
> systems. Jobs are imported manually by pasting their description or URL.

## Repository layout

```
.
├── backend/        FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL + pgvector
├── frontend/       Vite · React · TypeScript · Tailwind · shadcn/ui · React Query
├── docs/           Architecture, ERD, roadmap
├── docker-compose.yml
└── Makefile
```

## Quickstart (Docker)

```bash
cp .env.example .env
make up               # builds and starts postgres + backend + frontend
make migrate          # apply Alembic migrations
make seed             # optional: create a demo user
```

- Frontend: <http://localhost:5173>
- Backend:  <http://localhost:8000>
- API docs: <http://localhost:8000/docs>

## Local development (without Docker)

```bash
make backend-dev      # uvicorn with reload
make frontend-dev     # vite dev server
```

## Import a job from a screenshot

Paste-as-text isn't always practical — Upwork posts on mobile, modal popovers,
internal screenshots. The platform accepts an Upwork job-post screenshot and
extracts the fields via the configured multimodal AI provider.

- `POST /api/v1/jobs/import-image` (multipart): `image` file + optional
  `source_url`. PNG / JPEG / WebP up to 10 MB.
- Response carries the persisted [`Job`](backend/app/application/dto/job_dto.py)
  + a structured `preview` (mandatory + nice-to-have skills, project
  type/duration, experience level, location, pre-application questions, etc).
- Frontend: **Import from screenshot** button on `/jobs` → drop-zone page at
  `/jobs/import` with file preview, optional Upwork URL, and success
  navigation to the new Job Detail.
- Mock provider behaviour: returns a clearly-labeled placeholder payload
  (title flags itself as "mock provider — switch to OpenAI/Claude for real
  extraction"). Set `AI_PROVIDER=openai` or `AI_PROVIDER=claude` with a key
  to enable actual extraction.

The structured extras (skills, questions, project type) are folded back into
`Job.description` so the existing Phase-2 analyzer treats screenshot-imported
jobs identically to manually pasted ones.

## Status

- **Phase 1 — Foundation** ✅ Clean Architecture skeleton, full Postgres schema,
  JWT auth, Jobs CRUD, Docker, CI.
- **Phase 2 — AI Job Analyzer + Opportunity Scoring** ✅ Mock/OpenAI/Claude
  providers, structured JSON analysis, deterministic 0–100 scoring with
  Strong-Apply / Apply / Maybe / Skip recommendation, "Analyze job" on the
  Job Detail page.
- **Phase 3 — Portfolio Knowledge Base + Semantic Matching** ✅ Portfolio CRUD,
  Mock/OpenAI embedding providers, pgvector storage, hybrid score
  (semantic·0.6 + skills·0.25 + domain·0.10 + strategic·0.05), "Match
  portfolio" on the Job Detail page.
- **Phase 4 — Resume Library + Resume Recommendation** ✅ Structured resume
  profiles with CRUD, shared embedding pipeline, hybrid recommendation
  (semantic·0.55 + skill_overlap·0.30 + domain·0.10 + seniority·0.05),
  "Recommend resume" on the Job Detail page with fit reasons, missing/weak
  skills, and suggested positioning.
- **Phase 5 — Proposal Generator + Quality Review** ✅ Tailored proposal
  generation grounded in analysis + matched portfolio + recommended resume,
  with a deterministic 100-point quality review (8 dimensions + warnings).
  "Generate proposal" on the Job Detail page with inline edit, save, copy,
  and re-run review.
- **Phase 6 — Application Tracker + Outcome Snapshots** ✅ Turn a proposal
  into an application with an immutable snapshot of the job, opportunity
  score, proposal body, resume, and portfolio. State machine across
  draft → applied → viewed → interview → offer → won → completed (plus
  rejected / withdrawn). Kanban UI on `/applications`.
- **Phase 7 — Analytics Dashboard** ✅ Read-only dashboard computed from
  snapshots + history: overview cards, funnel + rates, score effectiveness,
  proposal quality effectiveness, technology / domain / budget performance,
  revenue (incl. month-over-month line chart), time-to-status percentiles,
  and a recent-activity feed. Date-range filter; pure CTE-free Python
  aggregation per the no-materialized-views constraint.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for Phases 8–9.

## Phase 2 highlights

- `AIProvider` protocol in [`app/domain/providers`](backend/app/domain/providers/ai_provider.py)
  with three implementations: `MockAIProvider` (default, no network),
  `OpenAIProvider`, `ClaudeProvider`. Selected via `AI_PROVIDER=mock|openai|claude`.
- Strict Pydantic v2 schema for the analyzer output in
  [`app/application/dto/analysis_dto.py`](backend/app/application/dto/analysis_dto.py).
  Free-text parsing is forbidden — providers return JSON, we validate it, no
  exceptions.
- Deterministic scoring engine in
  [`app/application/services/scoring_service.py`](backend/app/application/services/scoring_service.py)
  with eight pure dimension functions summing to 100, configurable via
  [`FreelancerProfile`](backend/app/domain/profiles/freelancer_profile.py).
- Analysis + score are upserted into `job_analyses` and `opportunity_scores`
  (Alembic migration `0002_phase2_analysis_scoring`).
- Endpoints:
  - `POST /api/v1/jobs/{job_id}/analyze`
  - `POST /api/v1/jobs/{job_id}/reanalyze`
  - `GET  /api/v1/jobs/{job_id}/analysis`
- Frontend "Analyze job" button on Job Detail renders score card, breakdown,
  summary, extracted skills/technologies, risks, red/green flags, and
  questions-to-ask-the-client.

### Switching providers

```bash
# offline-safe default (heuristic, no network)
AI_PROVIDER=mock

# real LLM
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini       # optional override

# or Anthropic
AI_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-6 # optional override
```

The mock provider stays useful even with real keys configured: tests run
against it, and you can flip back to it for offline demos without code changes.

## Phase 3 highlights

- `EmbeddingProvider` protocol in
  [`app/domain/providers/embedding_provider.py`](backend/app/domain/providers/embedding_provider.py)
  with two implementations:
  [`MockEmbeddingProvider`](backend/app/infrastructure/ai/mock_embedding_provider.py)
  (deterministic feature-hashing, unit length, 1536-d — no network) and
  [`OpenAIEmbeddingProvider`](backend/app/infrastructure/ai/openai_embedding_provider.py)
  (text-embedding-3-small by default, normalized on the way out).
- Embeddings persist via the polymorphic `embeddings` table from Phase 1 —
  `owner_type ∈ {'portfolio','job'}`, scoped by `model_id` so providers never
  collide.
- [`PortfolioService`](backend/app/application/services/portfolio_service.py)
  re-embeds on every create / update; lazy `ensure_embedding` covers portfolios
  created before the current provider was selected.
- Hybrid matching in
  [`PortfolioMatchingService`](backend/app/application/services/portfolio_matching_service.py):
  `0.60·semantic + 0.25·skill_overlap + 0.10·domain_overlap + 0.05·strategic`.
  Each match comes back with reasons, relevant skills/domains, and suggested
  talking points so the UI doesn't have to invent them.
- Endpoints:
  - `POST /api/v1/portfolio`, `GET /api/v1/portfolio`,
    `GET /api/v1/portfolio/{id}`, `PUT /api/v1/portfolio/{id}`,
    `DELETE /api/v1/portfolio/{id}`
  - `POST /api/v1/jobs/{job_id}/match-portfolio?top_n=5`
  - `GET  /api/v1/jobs/{job_id}/portfolio-matches?top_n=5`
- Frontend: full `/portfolio` list + create/edit/delete pages, plus a
  **Match portfolio** button on Job Detail that renders ranked match cards
  (score, component bars, reasons, talking points).
- The seed script now inserts four realistic portfolios (Customer 360 Analytics,
  LinkedIn Data Portability POC, Arabic RAG Platform, Retool Marketplace Admin).

## Phase 4 highlights

- Migration `0004_phase4_resume` reshapes the Phase-1 placeholder `resumes`
  table: rename `label`→`title`, drop `content`/`file_url`/`is_default`, add
  `target_role`, `summary`, `seniority_level`, `primary_skills`,
  `secondary_skills`, `industries`, `domains`, `achievements`,
  `project_highlights`, `keywords`, `notes`.
- [`ResumeService`](backend/app/application/services/resume_service.py) mirrors
  `PortfolioService` — CRUD + embed-on-write with the same lazy
  `ensure_embedding` for late provider switches; reuses the Phase-3
  `EmbeddingProvider` and the polymorphic `embeddings` table with
  `owner_type='resume'`.
- [`ResumeRecommendationService`](backend/app/application/services/resume_recommendation_service.py)
  hybrid score:
  `0.55·semantic + 0.30·skill_overlap + 0.10·domain_overlap + 0.05·seniority`.
  Skill overlap is asymmetric and weighted (primary = 1.0, secondary = 0.5);
  seniority alignment uses an ordered `junior < mid < senior < lead < staff <
  principal` scale.
- Endpoints:
  - `POST /api/v1/resumes`, `GET /api/v1/resumes?search=&domain=&skill=`,
    `GET /api/v1/resumes/{id}`, `PUT /api/v1/resumes/{id}`,
    `DELETE /api/v1/resumes/{id}`
  - `POST /api/v1/jobs/{job_id}/recommend-resume?top_n=3`
  - `GET  /api/v1/jobs/{job_id}/resume-recommendations?top_n=3`
- Frontend: full `/resumes` list + create/edit/delete pages, plus a
  **Recommend resume** card on Job Detail showing the recommended profile,
  alternatives, fit reasons, missing/weak skills, and template-driven
  positioning suggestions.
- The seed script now inserts five resume profiles (AI/LLM, Python Backend,
  Full-Stack SaaS, Architecture/Audit, Engineering Manager).

## Phase 5 highlights

- Migration `0005_phase5_proposal` reshapes the Phase-1 placeholder
  `proposals` table — rename `provider`→`model_provider`, `model`→`model_name`,
  drop `draft_body` + numeric `score`, add `title`, `short_body`, structured
  `questions` / `milestones` / `delivery_approach` / `risk_notes`,
  `portfolio_ids`, `resume_id` FK, `quality_score` + breakdown + warnings,
  `prompt_version`, `raw_response`.
- Generalized `AIProvider.analyze_job` → `AIProvider.complete_json` so a
  single port serves analyzer and proposal calls. The MockAIProvider routes
  by a `--- PROPOSAL ASSIGNMENT ---` marker in the user prompt.
- [`proposal_prompts.py`](backend/app/application/services/proposal_prompts.py)
  carries the system prompt, `PROMPT_VERSION = "proposal-v1"`, and the
  `BANNED_PHRASES` tuple. The same tuple is enforced by the deterministic
  review — prompt and review can never drift.
- [`ProposalGenerationService`](backend/app/application/services/proposal_generation_service.py)
  orchestrates the pipeline: load job → require analysis + score → fetch
  fresh portfolio matches and resume recommendations → build a compact
  prompt context (truncated job description, top-2 portfolios, top-1 resume)
  → `complete_json` → Pydantic validation → review → upsert into `proposals`.
- [`ProposalReviewService`](backend/app/application/services/proposal_review_service.py)
  scores 8 deterministic dimensions summing to 100:
  specificity·20 + relevance·20 + portfolio_evidence·15 + clarity·15 +
  brevity·10 + non_generic_wording·10 + risk_awareness·5 + call_to_action·5.
  Each dimension also surfaces concrete warnings.
- Endpoints:
  - `POST /api/v1/jobs/{id}/proposals/generate`
  - `GET  /api/v1/jobs/{id}/proposals/latest`
  - `GET  /api/v1/jobs/{id}/proposals`
  - `GET  /api/v1/proposals/{id}`
  - `PUT  /api/v1/proposals/{id}`
  - `DELETE /api/v1/proposals/{id}`
  - `POST /api/v1/proposals/{id}/review`
- Frontend: a **Proposal** card on Job Detail with editable headline / body /
  short version, copy buttons, milestones, questions, delivery approach,
  risk notes, the 8-dimension quality breakdown, and warnings. Editing the
  body and re-running the review re-scores the proposal in place.

## Phase 6 highlights

- Migration `0006_phase6_application` extends `applications` with per-status
  timestamps (`viewed_at`, `interview_at`, `offer_at`, `won_at`, `rejected_at`,
  `withdrawn_at`, `completed_at`), `contract_amount`, `client_response`,
  `rejection_reason`, `portfolio_ids`, and an immutable `snapshot` JSONB.
  The `application_status` enum gains `draft` and `offer` values;
  `application_history` gains a `user_id` FK and `changed_at` is renamed to
  `created_at`.
- [`application_state_machine.py`](backend/app/domain/services/application_state_machine.py)
  in the domain layer encodes the legal transitions. Self-transitions and any
  move out of a terminal status are rejected. The frontend exposes the same
  table at `APPLICATION_STATUS_TRANSITIONS` so the UI only shows the buttons
  the backend will accept.
- [`application_snapshot.py`](backend/app/application/services/application_snapshot.py)
  assembles the snapshot at submission time — by **value**, not by FK — so
  later edits to the job, resume, or portfolio rows can never rewrite history.
  The snapshot captures the job, opportunity score + breakdown, the proposal
  body + quality, the resume with its `suggested_positioning` from the
  recommendation the user saw, and the portfolio entries with their match
  scores and talking points.
- [`ApplicationService`](backend/app/application/services/application_service.py)
  orchestrates `create_from_proposal`, status transitions (every move writes
  an `application_history` row), detail patches, and listing. Duplicate-active
  applications per job are blocked unless the existing one is in a terminal
  state.
- Endpoints:
  - `POST   /api/v1/applications/from-proposal/{proposal_id}`
  - `GET    /api/v1/applications?status=&search=&limit=&offset=`
  - `GET    /api/v1/applications/{id}`
  - `PATCH  /api/v1/applications/{id}/status`
  - `PATCH  /api/v1/applications/{id}`
  - `GET    /api/v1/applications/{id}/history`
  - `DELETE /api/v1/applications/{id}`
- Frontend: `/applications` Kanban (one column per status), per-application
  detail page with status transition buttons + timeline + full snapshot
  viewer, plus a **Mark as Applied** button on the Job Detail proposal card
  that flips to a "Applied · {status}" link once an application exists.
- The seed script optionally analyzes the demo job, generates a proposal,
  and creates one applied application for the demo user. Idempotent.

## Phase 7 highlights

- Outcome definitions are centralized in
  [`app/domain/analytics/definitions.py`](backend/app/domain/analytics/definitions.py)
  — `is_interviewed` is inclusive (a `won` app counts as interviewed),
  `is_lost` covers rejected + withdrawn, `is_active` covers
  applied/viewed/interview/offer.
- All extraction + bucketing logic is pure and lives in
  [`analytics_extraction.py`](backend/app/application/services/analytics_extraction.py):
  score/quality buckets, budget bucket from the snapshot's job.budget text,
  and a regex-with-word-boundary technology matcher that handles `.NET`,
  `C++`, etc. The known-skills dictionary is fixed per the spec.
- [`AnalyticsService`](backend/app/application/services/analytics_service.py)
  composes 11 sections (overview, funnel, outcomes, score & quality
  effectiveness, tech, domain, budget, revenue, time-to-status, recent
  activity) in pure Python. Per the spec we avoid materialized views; per-user
  application sets are small and a single Postgres round-trip pulls them.
- Endpoint: `GET /api/v1/analytics/dashboard?from_date=&to_date=`. Dates are
  inclusive at the day boundary and filter by `applications.created_at`.
- Frontend dashboard at `/analytics` with Recharts for the budget bar +
  monthly-revenue line. Empty-state handling per section so the UI is
  meaningful from the first application onward.
- Seed now creates ten varied demo applications (different statuses, scores,
  domains, budgets, contract amounts, and back-dated timestamps across a
  ~7-month range) so the dashboard has something to plot.
