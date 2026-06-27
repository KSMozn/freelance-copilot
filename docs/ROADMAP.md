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

## Phase 3 — Portfolio & Embeddings

- Portfolio CRUD (UI + API).
- Embedding service: enqueue embed jobs on portfolio create/update and on
  job analysis completion; writes to the `embeddings` table.
- Semantic match endpoint: `GET /portfolio/match?job_id=...` returns top-K
  portfolios with cosine similarity scores.
- UI: portfolio library page + match panel on job detail.

---

## Phase 4 — Scoring v2 (embeddings + per-user profile)

Builds on the Phase 2 scoring engine:

- Persist a per-user `FreelancerProfile` (`scoring_configs` table) so each user
  edits their own strong skills / domains / strategic priorities and per-
  dimension weights from the UI.
- Upgrade `TechnicalFitScorer` to use embedding cosine similarity (from
  Phase 3) rather than substring matching.
- Add a `PortfolioCoverageScorer` once portfolio embeddings exist.
- Surface a score badge on the Jobs list card and the dashboard.

---

## Phase 5 — Resume Library + AI Recommender

- Resume CRUD + default-resume rule.
- `ResumeRecommender` ranks user's resumes against the job's required skills.
- UI: resume library page + recommended-resume chip on job detail.

---

## Phase 6 — Proposal Generator

- `ProposalService` builds a prompt that injects:
  - the job analysis,
  - matching portfolio bullets,
  - selected resume highlights,
  - user voice/style notes.
- Streams the proposal to the UI; user edits inline; final saved to `proposals`.
- AI self-evaluation pass scores the draft (used to flag generic wording).

---

## Phase 7 — Application Tracker

- Create application from a proposal (`POST /applications`).
- State machine: applied → viewed → interview → rejected | won → completed.
- `application_history` writes on every transition.
- UI: applications board (Kanban) + per-application timeline.

---

## Phase 8 — Analytics Dashboard

- Materialized views or computed-on-read endpoints for:
  - win rate (overall, by technology, by domain),
  - average proposal score,
  - average proposals count on jobs you won,
  - budget distribution,
  - interview conversion rate,
  - revenue, average project size.
- UI: dashboard page with charts (Recharts).

---

## Phase 9 — Learning Loop

- Periodic job: for each won/lost outcome, write back features into a
  training set and re-fit the dimension weights in the scoring config.
- A/B holdout to verify lifts before adopting new weights.

---

## Phase 10 — Hardening

- Rate-limit & quota on LLM calls per user.
- Cost dashboard.
- Audit log of every AI call (prompt hash, tokens, latency, cost).
- Playwright E2E coverage for golden paths.
- GitHub Actions: lint, type-check, test, build, push images.
