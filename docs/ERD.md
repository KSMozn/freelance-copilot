# Entity Relationship Diagram

```
┌─────────────┐        ┌──────────────┐
│   users     │ 1───n  │     jobs     │
└─────────────┘        └──────────────┘
       │                      │
       │                      │ 1
       │ 1                    │
       │                      n
       │                ┌──────────────┐ 1   1 ┌──────────────────┐
       │                │ applications │───────│ job_analyses     │
       │                └──────────────┘       └──────────────────┘
       │                      │ n                       │
       │                      │                         │ optional
       │                      │ 1                       │
       │                ┌──────────────┐         ┌──────────────┐
       │                │  proposals   │         │    clients   │
       │                └──────────────┘         └──────────────┘
       │
       │ 1     n  ┌──────────────┐
       ├──────────│  portfolios  │
       │          └──────────────┘
       │ 1     n  ┌──────────────┐
       ├──────────│   resumes    │
       │          └──────────────┘
       │ 1     n  ┌──────────────┐
       └──────────│     tags     │
                  └──────────────┘

  application_history (n) ─── applications (1)
  embeddings (polymorphic by owner_type/owner_id)
  skills (master list)  ─── jobs_skills, portfolio_skills (m2m)
```

## Tables

### users
| column        | type           | notes                          |
|---------------|----------------|--------------------------------|
| id            | uuid PK        |                                |
| email         | citext UNIQUE  |                                |
| password_hash | text           | bcrypt                         |
| full_name     | text           |                                |
| is_active     | bool           | default true                   |
| is_superuser  | bool           | default false                  |
| created_at    | timestamptz    |                                |
| updated_at    | timestamptz    |                                |

### jobs
Imported job posts. Versioned via `source_hash` + `version`.

| column          | type            | notes                                                  |
|-----------------|-----------------|--------------------------------------------------------|
| id              | uuid PK         |                                                        |
| user_id         | uuid FK→users   |                                                        |
| title           | text            |                                                        |
| description     | text            | original pasted text                                   |
| source_url      | text NULL       |                                                        |
| budget_type     | enum(fixed,hourly) NULL |                                                |
| budget_min      | numeric NULL    |                                                        |
| budget_max      | numeric NULL    |                                                        |
| currency        | text            | default 'USD'                                          |
| proposal_count  | int NULL        | as reported at import                                  |
| client_id       | uuid FK→clients NULL |                                                   |
| status          | enum(new, shortlisted, applied, ignored, archived) |                            |
| source_hash     | text            | sha256 of normalized description, used for versioning  |
| version         | int             | starts at 1; same hash → no new row                    |
| imported_at     | timestamptz     |                                                        |
| created_at      | timestamptz     |                                                        |
| updated_at      | timestamptz     |                                                        |

### job_analyses *(Phase 2)*
Structured AI extraction.

| column                    | type        | notes                            |
|---------------------------|-------------|----------------------------------|
| id                        | uuid PK     |                                  |
| job_id                    | uuid FK     | UNIQUE                           |
| required_skills           | jsonb       |                                  |
| preferred_skills          | jsonb       |                                  |
| seniority                 | text        |                                  |
| business_domain           | text        |                                  |
| complexity                | enum(low, medium, high) |                          |
| hidden_requirements       | jsonb       |                                  |
| technologies              | jsonb       |                                  |
| expected_deliverables     | jsonb       |                                  |
| estimated_hours_min       | int NULL    |                                  |
| estimated_hours_max       | int NULL    |                                  |
| risk_level                | enum(low, medium, high) |                          |
| communication_required    | text        |                                  |
| raw_response              | jsonb       | provider response for audit      |
| provider                  | text        | 'openai' \| 'claude'             |
| model                     | text        |                                  |
| created_at                | timestamptz |                                  |

### clients
| column         | type    | notes                                |
|----------------|---------|--------------------------------------|
| id             | uuid PK |                                      |
| user_id        | uuid FK |                                      |
| display_name   | text    | client name or handle if available   |
| country        | text NULL |                                    |
| total_spent    | numeric NULL |                                 |
| hire_rate      | numeric NULL |                                 |
| rating         | numeric NULL |                                 |
| notes          | text    |                                      |

### portfolios
| column            | type      |
|-------------------|-----------|
| id                | uuid PK   |
| user_id           | uuid FK   |
| name              | text      |
| description       | text      |
| github_url        | text NULL |
| live_url          | text NULL |
| business_domains  | text[]    |
| features          | jsonb     |
| highlight         | bool      |

### resumes
| column        | type    | notes                                  |
|---------------|---------|----------------------------------------|
| id            | uuid PK |                                        |
| user_id       | uuid FK |                                        |
| label         | text    | e.g. 'Python', 'AI', 'Engineering Mgr' |
| content       | text    | markdown / structured                  |
| file_url      | text NULL |                                      |
| is_default    | bool    |                                        |

### skills *(master list)*
| column | type | notes |
|--------|------|-------|
| id     | uuid PK | |
| name   | text UNIQUE | normalized lowercase |
| kind   | enum(technical, domain, soft) | |

### jobs_skills *(m2m)*  ·  portfolio_skills *(m2m)*  ·  resume_skills *(m2m)*
`(parent_id, skill_id, weight numeric)`

### applications
| column          | type      | notes |
|-----------------|-----------|-------|
| id              | uuid PK   |       |
| user_id         | uuid FK   |       |
| job_id          | uuid FK   |       |
| proposal_id     | uuid FK NULL |    |
| resume_id       | uuid FK NULL |    |
| status          | enum(applied, viewed, interview, rejected, won, completed, withdrawn) |
| connects_spent  | int NULL  |       |
| bid_amount      | numeric NULL |    |
| applied_at      | timestamptz |     |
| outcome_at      | timestamptz NULL | |
| notes           | text NULL |       |

### application_history
Append-only log of status transitions on an application.

| column         | type        |
|----------------|-------------|
| id             | uuid PK     |
| application_id | uuid FK     |
| from_status    | text NULL   |
| to_status      | text        |
| changed_at     | timestamptz |
| note           | text NULL   |

### proposals
| column         | type      | notes                          |
|----------------|-----------|--------------------------------|
| id             | uuid PK   |                                |
| user_id        | uuid FK   |                                |
| job_id         | uuid FK   |                                |
| body           | text      | final proposal text            |
| draft_body     | text NULL | last AI draft before edits     |
| provider       | text NULL | for AI drafts                  |
| model          | text NULL |                                |
| score          | numeric NULL | AI self-evaluation          |
| created_at     | timestamptz |                              |

### application_portfolios *(m2m: application ↔ portfolios used in proposal)*
`(application_id, portfolio_id, order int)`

### tags
User-defined labels on jobs, portfolios, resumes (polymorphic via `owner_type`).

### embeddings
| column      | type           | notes                                                |
|-------------|----------------|------------------------------------------------------|
| id          | uuid PK        |                                                      |
| owner_type  | text           | 'job' \| 'portfolio' \| 'resume' \| 'proposal'       |
| owner_id    | uuid           |                                                      |
| model       | text           | e.g. 'text-embedding-3-small'                        |
| dim         | int            |                                                      |
| vector      | vector(1536)   | pgvector                                             |
| created_at  | timestamptz    |                                                      |

Index: `ivfflat (vector vector_cosine_ops)`. Unique `(owner_type, owner_id, model)`.

## Phase ownership

- Phase 1 creates **every** table in the baseline migration. Columns related to
  AI-derived data are populated starting in Phase 2.
- Phase 2 fills `job_analyses`, `embeddings` (job + portfolio).
- Phase 3 wires `application_portfolios`, scoring runs, analytics views.
