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

JWT (HS256 in dev, RS256-ready in `core/security.py`).

- `POST /api/v1/auth/register` — create user, return access + refresh tokens.
- `POST /api/v1/auth/login` — verify credentials, return tokens.
- `POST /api/v1/auth/refresh` — rotate access token from refresh token.
- `GET  /api/v1/auth/me` — current user.

Passwords are hashed with `bcrypt` via `passlib`. Tokens carry `sub` (user id),
`type` (`access`/`refresh`), `exp`, `iat`.

## AI Provider Abstraction (Phase 2+)

```python
class LLMProvider(Protocol):
    async def complete_json(
        self, *, system: str, user: str, schema: type[BaseModel]
    ) -> BaseModel: ...
```

Two implementations live in `infrastructure/ai/`: `OpenAIProvider`, `ClaudeProvider`.
Selection is configuration-driven (`AI_PROVIDER=openai|claude`). All prompts
return strict JSON validated against a Pydantic schema — no free-text parsing.

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
