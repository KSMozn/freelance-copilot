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

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for Phases 4–10.

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
