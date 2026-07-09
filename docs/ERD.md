# Entity Relationship Diagram

> **Live vs dormant surfaces (2026-07).** The live Careero product (student CV
> wizard + PersonaArmory admin console) uses: `users`, `email_otp_codes`,
> `refresh_tokens`, `uploaded_files` (profile photos), `student_profiles`,
> `student_profile_entries`, `cv_templates`, `feedback_entries`,
> `usage_events`, and the separate `admin_users` identity space.
> (`persona_archetypes` / `personas` still gain a row per user via
> `ensure_primary` at auth.) Every other table belongs to the **dormant**
> professional surface — its backend endpoints still run, but the frontend
> routes are not registered.

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

  email_otp_codes (n) ─── users (1) by email (not FK)   [Phase A]

  skill_catalog (1) ─── user_skills (n) ─── users (1)               [Phase B]
  experiences (n) ─── users (1)                                     [Phase B]
  projects (n) ─── users (1), → repositories | portfolios          [Phase B]
  experience_skills, project_skills (m2m → skill_catalog)           [Phase B]
  experience_achievements, project_achievements (n) ─── parent (1)  [Phase B]

  persona_archetypes (1) ─── personas (n) ─── users (1)             [Phase C]

  uploaded_files (n) ─── users (1)                                  [Phase D]
  cv_uploads (n) ─── users (1) ↔ personas (hint)                    [Phase D]
  linkedin_snapshots (n) ─── users (1) → uploaded_files             [Phase D]
  certificates (n) ─── users (1) → uploaded_files                   [Phase D]
  content_items (n) ─── users (1)                                   [Phase D]

  match_reports (n) ─── users (1) → jobs → personas (one per pair)  [Phase E]

  outputs (n) ─── users (1) → personas, jobs                        [Phase F]

  recruiter_interactions (n) ─── applications (1)                   [Phase H]
  interview_events (n) ─── applications (1)                         [Phase H]
  follow_up_reminders (n) ─── applications (1)                      [Phase H]
  applications.{resume_output_id, cover_letter_output_id} → outputs [Phase H]

  student_profiles (1) ─── users (1) ─── student_profile_entries (n) [Phase K]
  usage_events (n) ─── users (1) SET NULL — append-only activity log [Phase L]
  admin_users — separate identity space, no FK to users              [Phase L]
  cv_templates — seeded registry; student_profiles.cv_template_slug  [Phase L]
  feedback_entries (n) ─── users (1)                                 [Phase M]
  refresh_tokens — one per minted refresh JWT; no FK (user or admin) [Phase P]
```

## Tables

### users
| column            | type           | notes                                                        |
|-------------------|----------------|--------------------------------------------------------------|
| id                | uuid PK        |                                                              |
| email             | citext UNIQUE  |                                                              |
| password_hash     | text NULL      | bcrypt — nullable (Phase A): OTP-only accounts have no password |
| full_name         | text           |                                                              |
| is_active         | bool           | default true                                                 |
| is_superuser      | bool           | default false                                                |
| email_verified_at | timestamptz NULL | *(Phase A)* set when an OTP is successfully consumed      |
| last_login_at     | timestamptz NULL | *(Phase A)* touched on every successful auth              |
| selected_persona_kind | varchar(32) | *(Phase K)* `'professional'` (default) routes to the existing app; `'student'` routes to the wizard at `/student`. Index `ix_users_persona_kind`. |
| created_at        | timestamptz    |                                                              |
| updated_at        | timestamptz    |                                                              |

### email_otp_codes *(Phase A)*
Hashed 6-digit codes used for passwordless signup / sign-in / email-change verification.

| column       | type                                          | notes                                              |
|--------------|-----------------------------------------------|----------------------------------------------------|
| id           | uuid PK                                       |                                                    |
| email        | citext                                        | indexed; not FK — allows pre-registration codes    |
| code_hash    | text                                          | bcrypt hash of the 6-digit code (never plaintext)  |
| purpose      | enum(login, register, email_change)           |                                                    |
| expires_at   | timestamptz                                   | typically now + 10 min                             |
| consumed_at  | timestamptz NULL                              | set on successful verify; prevents reuse           |
| attempts     | smallint                                      | default 0; cap at 5 incorrect submissions          |
| ip_address   | inet NULL                                     | recorded at issuance for abuse forensics           |
| user_agent   | text NULL                                     | recorded at issuance for abuse forensics           |
| created_at   | timestamptz                                   |                                                    |

Indexes:
- `(email, purpose, consumed_at)` — find the active code at verify time
- `(expires_at)` — cleanup job

### skill_catalog *(Phase B)*
Global, normalized skill master list. Replaces the loose JSONB skill strings
that lived on resumes / portfolios / repositories. Seeded with ~120 common
languages / frameworks / tools / platforms / databases / practices / soft
skills / leadership skills / domains; free-form user-added skills also land
here with `is_system_seeded = false`.

| column             | type                                                                          | notes                                              |
|--------------------|-------------------------------------------------------------------------------|----------------------------------------------------|
| id                 | uuid PK                                                                       |                                                    |
| slug               | text UNIQUE                                                                   | kebab-case canonical key, e.g. `postgresql`        |
| name               | text                                                                          | display name, e.g. `PostgreSQL`                    |
| category           | enum(language, framework, tool, platform, database, domain, soft, practice, leadership) | drives downstream weighting                |
| aliases            | jsonb (array of strings)                                                       | e.g. `["postgres", "psql", "pg"]`                 |
| is_system_seeded   | bool                                                                          | true for the seed list; false for user-added rows  |
| created_by_user_id | uuid FK→users NULL                                                            | who introduced the row (free-form add)             |
| created_at         | timestamptz                                                                   |                                                    |

Indexes: GIN on `aliases`; GIN trigram (`pg_trgm`) on `name` for fuzzy lookup.

### user_skills *(Phase B)*
The global per-user skill "pot." Personas (Phase C) project / weight rows
from this table rather than owning their own per-persona pot.

| column              | type                       | notes                                                                   |
|---------------------|----------------------------|-------------------------------------------------------------------------|
| id                  | uuid PK                    |                                                                         |
| user_id             | uuid FK→users CASCADE      |                                                                         |
| skill_id            | uuid FK→skill_catalog RESTRICT |                                                                     |
| proficiency         | smallint                   | 1–5; defaults to 3                                                      |
| years_experience    | numeric(4,1) NULL          | self-reported                                                           |
| sources             | jsonb                      | `{repo_ids, resume_ids, portfolio_ids, cv_upload_ids, manual, ai_suggested}` |
| evidence_count      | int                        | denormalized count across all source lists                              |
| is_active           | bool                       | default true                                                            |
| pinned              | bool                       | user-promoted in their persona view (Phase C surfaces this)             |
| last_evidence_date  | timestamptz NULL           |                                                                         |
| added_at            | timestamptz                |                                                                         |
| updated_at          | timestamptz                |                                                                         |

UNIQUE `(user_id, skill_id)`. Index `(user_id, proficiency DESC)`.

### experiences / experience_skills / experience_achievements *(Phase B)*
The "what I've done" facts. Populated from CV uploads / LinkedIn PDFs
(Phase D) or manual entry; empty after Phase B migrations until ingestion
lands. Personas can pin specific experiences for emphasis.

`experiences`: `id`, `user_id`, `company`, `role`, `location`, `employment_type`
(`full_time` | `contract` | `freelance` | `internship` | `part_time`),
`start_date`, `end_date` (NULL = current), `summary`, `source`
(`cv` | `linkedin` | `manual` | `backfill`), `source_ref` (UUID of the
originating record), timestamps.

`experience_skills`: m2m link to `skill_catalog` with optional `evidence_text`.

`experience_achievements`: per-experience measurable outcomes —
`statement`, `metric_value`, `metric_unit`, `evidence_text`.

### projects / project_skills / project_achievements *(Phase B)*
Unified "thing I built" — subsumes both `portfolios` and `repositories`.
The Phase B backfill creates one `projects` row per existing portfolio
(`origin = portfolio`, linked via `portfolio_id`) and per scanned
repository (`origin = repo`, linked via `repo_id`). New surfaces
(`origin = cv_extracted`, `origin = manual`) ride the same shape.

`projects`: `id`, `user_id`, `name`, `summary`, `role`, `period_start`,
`period_end`, `repo_id` FK→repositories SET NULL, `portfolio_id`
FK→portfolios SET NULL, `origin`
(`repo` | `portfolio` | `cv_extracted` | `manual`), timestamps.

`project_skills`, `project_achievements`: same shape as the experience
join tables.

### persona_archetypes *(Phase C)*
System-seeded persona templates. Immutable from user CRUD — only the
Alembic migration `0021_phase_c_seed_archetypes` upserts rows. Eleven
archetypes ship today (Individual Contributor, Senior Engineer, Tech
Lead, Staff Engineer, Principal Engineer, Engineering Manager, Director
of Engineering, AI Engineer, Solutions Architect, Consultant, Freelancer).

| column                          | type                                                                          | notes                                              |
|---------------------------------|-------------------------------------------------------------------------------|----------------------------------------------------|
| id                              | uuid PK                                                                       |                                                    |
| slug                            | text UNIQUE                                                                   | e.g. `tech_lead`                                   |
| name                            | text                                                                          | display name                                       |
| description                     | text                                                                          | one-liner shown on the archetype gallery card      |
| default_weights                 | jsonb                                                                         | scoring weights summing to 100                     |
| default_skill_category_weights  | jsonb                                                                         | per-category emphasis summing to 1.0               |
| default_proposal_tone           | enum(pragmatic, technical_deep, executive, consultative, empathetic)          |                                                    |
| default_target_roles            | jsonb (array of strings)                                                       | seed for the persona's `target_role` field         |
| default_seniority_band          | text NULL                                                                     | feeds resume↔job seniority alignment               |
| is_active                       | bool                                                                          | default true                                       |
| sort_order                      | smallint                                                                      | display order in the archetype gallery             |
| created_at                      | timestamptz                                                                   |                                                    |

### personas *(Phase C)*
Per-user instances of an archetype, freely customizable. JSONB columns
carry *overrides* on top of archetype defaults — merged at read time by
`PersonaProfileResolver` (persona wins).

| column                | type                       | notes                                                                                  |
|-----------------------|----------------------------|----------------------------------------------------------------------------------------|
| id                    | uuid PK                    |                                                                                        |
| user_id               | uuid FK→users CASCADE      |                                                                                        |
| archetype_id          | uuid FK→persona_archetypes RESTRICT |                                                                              |
| name                  | text                       | user-facing label                                                                      |
| target_role           | text NULL                  | e.g. "Tech Lead — Backend"                                                             |
| target_seniority      | text NULL                  | overrides archetype default                                                            |
| weights               | jsonb                      | scoring-weight overrides                                                               |
| skill_category_weights| jsonb                      | category-emphasis overrides                                                            |
| proposal_tone         | enum(proposal_tone) NULL   | override; NULL → use archetype default                                                 |
| strategic_priorities  | jsonb (array of strings)   | override; used by ScoringService strategic_value                                       |
| pinned_experience_ids | jsonb (array of UUID strings) | always surface these experiences regardless of recency                              |
| pinned_project_ids    | jsonb (array of UUID strings) | always surface these projects in matching                                            |
| pinned_skill_ids      | jsonb (array of UUID strings) | always surface these skills in `strong_skills`                                       |
| accent_color          | text NULL                  | hex string for the persona's topbar stripe (Phase C reserved; renders in Phase E)      |
| is_default            | bool                       | exactly one per user via partial unique index                                          |
| is_archived           | bool                       | soft-hide; the persona stays around for historical proposal/analysis references        |
| created_at            | timestamptz                |                                                                                        |
| updated_at            | timestamptz                |                                                                                        |

UNIQUE `(user_id, name)`. Partial UNIQUE
`(user_id) WHERE is_default = true` — keeps the invariant cheap and queryable.
Index `(user_id, is_archived)`.

### uploaded_files *(Phase D)*
Generic blob registry. Dedup is per-user via UNIQUE `(user_id, sha256)`.

| column        | type                  | notes                                |
|---------------|-----------------------|--------------------------------------|
| id            | uuid PK               |                                      |
| user_id       | uuid FK→users CASCADE |                                      |
| filename      | text                  |                                      |
| content_type  | text                  | MIME from the upload                 |
| size_bytes    | bigint                |                                      |
| storage_path  | text                  | local path (bind-mount volume)       |
| sha256        | char(64)              | also used for dedup                  |
| created_at    | timestamptz           |                                      |

### cv_uploads *(Phase D)*
A PDF / DOCX / pasted-text CV. The full pipeline lives in
`CvIngestService`: text extraction → LLM structuring → graph ingest.
`extracted_structure` holds the canonical structured JSON; `extracted_skills`
is the flattened skill-name list for fast UI rendering. Dedup is by
UNIQUE `(user_id, sha256)` — re-uploading the same file returns the
existing row.

| column              | type                                                | notes                                              |
|---------------------|-----------------------------------------------------|----------------------------------------------------|
| id                  | uuid PK                                             |                                                    |
| user_id             | uuid FK→users CASCADE                               |                                                    |
| persona_id          | uuid FK→personas SET NULL NULL                      | parsing hint; not a hard scoping boundary          |
| filename            | text                                                |                                                    |
| content_type        | text                                                |                                                    |
| size_bytes          | bigint                                              |                                                    |
| storage_path        | text NULL                                           | local blob path; NULL if write failed              |
| sha256              | char(64)                                            |                                                    |
| extracted_text      | text NULL                                           |                                                    |
| parse_status        | enum(pending, parsing, parsed, failed)              | drives the UI's progress pill                      |
| parse_error         | text NULL                                           | filled when parse_status = 'failed'                |
| extracted_structure | jsonb                                               | `{summary, experiences[], skills[]}` shape         |
| extracted_skills    | jsonb (array of strings)                            | flattened distinct skill names                     |
| resume_id           | uuid FK→resumes SET NULL NULL                       | optional link to a derived Resume row              |
| created_at          | timestamptz                                         |                                                    |
| updated_at          | timestamptz                                         |                                                    |

### linkedin_snapshots *(Phase D)*
A parsed LinkedIn "Save to PDF" export. Same pipeline shape as `cv_uploads`
but kept as its own table so future LinkedIn-specific structuring prompts
can land cleanly. Blob is referenced from the generic `uploaded_files`
registry.

| column              | type                                          | notes                                |
|---------------------|-----------------------------------------------|--------------------------------------|
| id                  | uuid PK                                       |                                      |
| user_id             | uuid FK→users CASCADE                         |                                      |
| file_id             | uuid FK→uploaded_files SET NULL NULL          | references the source PDF blob       |
| extracted_text      | text NULL                                     |                                      |
| extracted_structure | jsonb                                         | same shape as cv_uploads             |
| parse_status        | enum(pending, parsing, parsed, failed)        |                                      |
| parse_error         | text NULL                                     |                                      |
| parsed_at           | timestamptz NULL                              | set when parse_status transitions    |
| created_at          | timestamptz                                   |                                      |

### certificates *(Phase D)*
Self-attested credentials (with optional credential URL / file).

| column          | type                                          | notes                              |
|-----------------|-----------------------------------------------|------------------------------------|
| id              | uuid PK                                       |                                    |
| user_id         | uuid FK→users CASCADE                         |                                    |
| name            | text                                          | e.g. "AWS Solutions Architect"     |
| issuer          | text                                          | e.g. "Amazon Web Services"         |
| issued_date     | date NULL                                     |                                    |
| expiry_date     | date NULL                                     |                                    |
| credential_id   | text NULL                                     |                                    |
| credential_url  | text NULL                                     | verification link                  |
| file_id         | uuid FK→uploaded_files SET NULL NULL          | optional certificate PDF           |
| created_at      | timestamptz                                   |                                    |
| updated_at      | timestamptz                                   |                                    |

### content_items *(Phase D)*
Published artefacts that signal expertise — blog posts, talks, papers,
open-source projects. URL-only entries are fine; `raw_text` is optional
and reserved for future analysis (Phase G market-aware recommendations
will use it to detect declared expertise areas).

| column          | type                                                          | notes                          |
|-----------------|---------------------------------------------------------------|--------------------------------|
| id              | uuid PK                                                       |                                |
| user_id         | uuid FK→users CASCADE                                         |                                |
| type            | enum(blog_post, talk, paper, open_source)                     |                                |
| title           | text                                                          |                                |
| url             | text NULL                                                     |                                |
| published_date  | date NULL                                                     |                                |
| summary         | text NULL                                                     | 1-2 sentences                  |
| raw_text        | text NULL                                                     | optional full body             |
| created_at      | timestamptz                                                   |                                |
| updated_at      | timestamptz                                                   |                                |

### match_reports *(Phase E)*
Persisted persona-aware match analysis. One row per `(job, persona)` —
`MatchReportService` UPSERTs by that pair so re-runs don't pile up.

| column                  | type                                   | notes                                                  |
|-------------------------|----------------------------------------|--------------------------------------------------------|
| id                      | uuid PK                                |                                                        |
| user_id                 | uuid FK→users CASCADE                  | tenancy boundary                                       |
| job_id                  | uuid FK→jobs CASCADE                   |                                                        |
| persona_id              | uuid FK→personas CASCADE NULL          | NULL = pre-Phase-C "user-level" report                 |
| overall_match           | smallint                               | 0..100, weighted from the dimensions below             |
| technical_fit           | smallint                               | 0..100, importance-weighted skill coverage             |
| architecture_fit        | smallint                               | 0..100, best semantic match across portfolio + repos   |
| domain_fit              | smallint                               | 0..100, domain overlap                                 |
| leadership_fit          | smallint NULL                          | 0..100; NULL when the job carries no leadership signals|
| soft_skills_fit         | smallint NULL                          | 0..100; NULL when the job carries no soft signals      |
| interview_chance        | enum(low, medium, high)                | bucketed                                               |
| missing_critical_skills | jsonb (array of {name, importance, status}) | self-contained snapshot for diffing               |
| missing_recommendations | jsonb (array of GapRecommendation)     | `{skill, kind, suggestion, effort_estimate, priority}` |
| rationale               | jsonb (array of strings)               | one-line narrative bullets                             |
| profile_version         | text NULL                              | e.g. `persona:<uuid>` or `default-v1`                  |
| computed_at             | timestamptz                            |                                                        |

UNIQUE `(job_id, persona_id)`. Index `(user_id, job_id)`.

Recommendation `kind` is one of: `project_to_build`, `certification`,
`learning_resource`, `github_enhancement`, `experience_to_emphasize`.

### outputs *(Phase F)*
Unified "generated artifact" table — subsumes any AI-produced text about
a job (cover letter, Upwork proposal, recruiter reply, LinkedIn DM,
consulting proposal, screening answer, tailored resume). Per-kind
specialisation lives in the prompt template, not in extra tables.

| column            | type                                                                                                | notes                                                  |
|-------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------|
| id                | uuid PK                                                                                             |                                                        |
| user_id           | uuid FK→users CASCADE                                                                               |                                                        |
| persona_id        | uuid FK→personas SET NULL                                                                           | the lens that produced this output                     |
| job_id            | uuid FK→jobs CASCADE NULL                                                                           | nullable so kindless outputs (Phase J) fit here too    |
| kind              | enum(upwork_proposal, cover_letter, recruiter_reply, linkedin_message, consulting_proposal, screening_answer, resume_tailored) |                                  |
| title             | text NULL                                                                                           | filled for standalone docs; NULL for chat-style        |
| content_markdown  | text                                                                                                | the artifact in markdown                               |
| content_html      | text NULL                                                                                           | optional rendered HTML                                 |
| citations         | jsonb (array of Citation)                                                                           | each `{claim, evidence_type, evidence_id, evidence_label, snippet}` |
| metadata          | jsonb                                                                                               | `{profile_version, …}`                                 |
| tone              | text NULL                                                                                           | persona tone used at generation                        |
| ai_provider       | text NULL                                                                                           | e.g. `openai`, `mock`                                  |
| ai_model          | text NULL                                                                                           |                                                        |
| created_at        | timestamptz                                                                                         |                                                        |

Indexes: `(user_id, job_id)`, `(user_id, kind, created_at)`.

`Citation.evidence_type` ∈ `experience | project | repository |
certificate | content_item | skill`.

### recruiter_interactions *(Phase H)*
Every back-and-forth with a recruiter on a given application.

| column        | type                                                  | notes                                            |
|---------------|-------------------------------------------------------|--------------------------------------------------|
| id            | uuid PK                                               |                                                  |
| application_id| uuid FK→applications CASCADE                          |                                                  |
| user_id       | uuid FK→users CASCADE                                 | denormalized for tenant-scoped queries           |
| channel       | enum(email, linkedin, phone, in_person, other)        |                                                  |
| direction     | enum(inbound, outbound)                               | who reached out                                  |
| occurred_at   | timestamptz                                           |                                                  |
| contact_name  | text NULL                                             |                                                  |
| summary       | text NULL                                             | 1-line of what was said                          |
| raw_content   | text NULL                                             | optional full body (pasted email, DM, …)         |
| created_at    | timestamptz                                           |                                                  |

### interview_events *(Phase H)*
One row per scheduled interview round.

| column            | type                                                                                       | notes                                       |
|-------------------|--------------------------------------------------------------------------------------------|---------------------------------------------|
| id                | uuid PK                                                                                    |                                             |
| application_id    | uuid FK→applications CASCADE                                                               |                                             |
| user_id           | uuid FK→users CASCADE                                                                      |                                             |
| round_label       | text                                                                                       | "Hiring manager screen"                     |
| format            | enum(phone_screen, technical, system_design, behavioral, onsite, final, other)             |                                             |
| scheduled_at      | timestamptz NULL                                                                           |                                             |
| duration_minutes  | smallint NULL                                                                              | 5..600                                      |
| interviewer_names | text NULL                                                                                  | free-form CSV                               |
| interviewer_notes | text NULL                                                                                  | what they cared about                       |
| my_feedback       | text NULL                                                                                  | what I'd improve next time                  |
| outcome           | enum(pending, pass, fail, cancelled)                                                       |                                             |
| created_at, updated_at | timestamptz                                                                           |                                             |

### follow_up_reminders *(Phase H)*
A personal to-do list per application. The UI surfaces overdue + due-soon
items on the dashboard.

| column          | type                                                  | notes                                        |
|-----------------|-------------------------------------------------------|----------------------------------------------|
| id              | uuid PK                                               |                                              |
| application_id  | uuid FK→applications CASCADE                          |                                              |
| user_id         | uuid FK→users CASCADE                                 |                                              |
| due_at          | timestamptz                                           |                                              |
| channel         | enum(interaction_channel) NULL                        | optional reminder of *how* to follow up      |
| note            | text                                                  | the actual to-do                             |
| completed_at    | timestamptz NULL                                      | NULL = still open                            |
| created_at      | timestamptz                                           |                                              |

Indexes: `(application_id)`, `(user_id, due_at) WHERE completed_at IS NULL`
— the partial unique index keeps the "open reminders for user X" query
to a single index scan.

### applications *(Phase H additions)*
Two new FK columns:
- `resume_output_id` → `outputs.id` SET NULL — the exact tailored resume
  sent.
- `cover_letter_output_id` → `outputs.id` SET NULL — the exact cover
  letter sent.

Closes the loop with Phase F: "which version did I send for this
application?" is one read.

### student_profiles *(Phase K — 1:1 with user)*
| column            | type           | notes                                                        |
|-------------------|----------------|--------------------------------------------------------------|
| user_id           | uuid PK / FK→users.id | cascade on user delete                                |
| full_name         | text NULL      | wizard "Basics" step                                         |
| professional_email | text NULL     | separate from auth login email; rule-coached at entry        |
| phone             | text NULL      |                                                              |
| location          | text NULL      |                                                              |
| date_of_birth     | date NULL      | *(0032)* not rendered on the CV by default (age-bias risk)   |
| college           | text NULL      | wizard "Education" step                                      |
| department        | varchar(200) NULL | *(0029)* faculty/college line, e.g. "College of Computer & Information Sciences" |
| degree            | text NULL      | e.g. Bachelor of Science                                     |
| major             | text NULL      |                                                              |
| graduation_year   | smallint NULL  |                                                              |
| gpa               | numeric(3,2) NULL |                                                           |
| photo_file_id     | uuid NULL FK→uploaded_files.id | SET NULL on file delete                      |
| photo_offset_x    | smallint NOT NULL default 50 | *(Phase N, 0035)* 0–100 % → CSS `background-position` |
| photo_offset_y    | smallint NOT NULL default 50 | *(Phase N, 0035)* 0–100 % → CSS `background-position` |
| photo_zoom        | smallint NOT NULL default 100 | *(Phase N, 0035)* 100–300 % → CSS `background-size`; crop applied at display time only |
| summary           | text NULL      |                                                              |
| headline          | text NULL      |                                                              |
| links             | jsonb          | `{github, linkedin, website, portfolio}` — partial OK        |
| interests         | jsonb          | list[str]                                                    |
| career_pack       | jsonb NOT NULL default '{}' | *(Phase O, 0036)* generated LinkedIn/GitHub content + review state; URLs stay in `links` |
| completed_steps   | jsonb          | list of step slugs the wizard has saved                      |
| current_step      | varchar(64) NULL | step to resume on next visit                               |
| cv_template_slug  | varchar(64) NULL | *(Phase L, 0033)* chosen template; no FK to `cv_templates` — NULL falls back to first visible |
| created_at        | timestamptz    |                                                              |
| updated_at        | timestamptz    |                                                              |

### student_profile_entries *(Phase K — repeating wizard items)*
| column            | type           | notes                                                        |
|-------------------|----------------|--------------------------------------------------------------|
| id                | uuid PK        |                                                              |
| user_id           | uuid FK→users.id | cascade                                                    |
| kind              | enum `student_entry_kind` | `course / project / internship / volunteer / certificate / skill / award / extracurricular / language` — `internship` added by 0040 |
| title             | text           | required                                                     |
| organization      | text NULL      | school / employer / issuer                                   |
| start_date        | date NULL      |                                                              |
| end_date          | date NULL      |                                                              |
| is_current        | bool           | default false                                                |
| description       | text NULL      |                                                              |
| url               | text NULL      |                                                              |
| details           | jsonb          | kind-specific extras (e.g. `{tech_stack, proficiency, credits, grade, credential_id}`) |
| sort_order        | smallint       | default 0                                                    |
| created_at        | timestamptz    |                                                              |
| updated_at        | timestamptz    |                                                              |

Index: `ix_student_entries_user_kind (user_id, kind, sort_order)`.

### usage_events *(Phase L)*
Append-only log of every "meaningful" call — coach LLM calls, CV renders,
auth events, admin actions/impersonations. Emitted fire-and-forget via
`usage_event_service.fire()`; the admin Activity page paginates over it and
the Overview/funnel/LLM-spend cards aggregate over it. LLM calls stash
`prompt_tokens` / `completion_tokens` / `cost_usd` / `model` / `provider`
in `meta`.

| column        | type                                   | notes                                                    |
|---------------|----------------------------------------|----------------------------------------------------------|
| id            | uuid PK                                | `gen_random_uuid()` default                              |
| user_id       | uuid FK→users SET NULL NULL            | NULL for pre-auth / system / admin-issued events         |
| kind          | enum `usage_event_kind`                | see values below                                         |
| status        | enum `usage_event_status` (ok, error)  |                                                          |
| duration_ms   | int NULL                               |                                                          |
| error_message | text NULL                              |                                                          |
| meta          | jsonb NOT NULL default '{}'            | kind-specific extras (target_user_id, tokens, cost, …)   |
| created_at    | timestamptz                            |                                                          |

Indexes: `(created_at, kind)`, `(user_id, created_at)`.

`usage_event_kind` values (0030, extended by 0037 / 0039 / 0041):
`auth.register / auth.login / auth.otp_request / auth.otp_verify /
coach.draft_summary / coach.proofread / coach.photo / coach.text /
coach.email / cv.preview / cv.pdf / admin.impersonate / admin.action /
error` + `career_pack.linkedin.generate / career_pack.linkedin.review /
career_pack.github.generate / career_pack.github.review` *(0037)* +
`cv.docx` *(0039)* + `coach.internship` *(0041)*.

### admin_users *(Phase L)*
Completely separate identity space from `users` — the same email can exist
on both sides with independent passwords and lifecycles. Admin JWTs carry
`pt=admin`; user and admin tokens can't access each other's resources. No
self-registration: rows are seeded via the `create_admin` job. The old
`users.is_superuser` column is vestigial.

| column        | type            | notes                              |
|---------------|-----------------|------------------------------------|
| id            | uuid PK         | `gen_random_uuid()` default        |
| email         | citext UNIQUE   | indexed; independent of users.email|
| password_hash | varchar(255)    | password-only login (no OTP)       |
| full_name     | varchar(255) NULL |                                  |
| is_active     | bool            | default true                       |
| last_login_at | timestamptz NULL |                                   |
| created_at    | timestamptz     |                                    |
| updated_at    | timestamptz     |                                    |

### cv_templates *(Phase L)*
Registry of the bundled CV templates students pick in the Preview step.
Rows are seeded by migration 0033 (`classic / modern / minimal / academic /
creative`) and correspond 1:1 to Jinja files under
`app/application/templates/student_cv/` — never inserted via the UI. Admins
toggle visibility / ordering from the admin panel.

| column       | type              | notes                                  |
|--------------|-------------------|----------------------------------------|
| slug         | varchar(64) PK    | must match a physical Jinja file       |
| display_name | varchar(120)      |                                        |
| description  | text              | default ''                             |
| is_visible   | bool              | default true; admin-toggled            |
| sort_order   | int               | default 100; admin-ordered             |
| created_at   | timestamptz       |                                        |
| updated_at   | timestamptz       |                                        |

### feedback_entries *(Phase M)*
One table for both feedback surfaces, discriminated by `kind`:
`general` (free-text from the /feedback page — fires an immediate admin
email) and `post_download` (1–5 star survey after a CV download — rolls
into the daily report only).

| column        | type                                    | notes                                                  |
|---------------|-----------------------------------------|--------------------------------------------------------|
| id            | uuid PK                                 | `gen_random_uuid()` default                            |
| user_id       | uuid FK→users CASCADE                   |                                                        |
| kind          | enum `feedback_kind` (general, post_download) |                                                  |
| rating        | smallint NULL                           | 1–5 stars for post_download; NULL for general          |
| message       | text NULL                               | required for general; optional survey comment          |
| template_slug | varchar(64) NULL                        | which CV template the survey followed                  |
| meta          | jsonb NOT NULL default '{}'             | carries `resolved_by_admin_id` / `resolved_by_email`   |
| created_at    | timestamptz                             |                                                        |
| resolved_at   | timestamptz NULL                        | *(0042)* NULL = needs attention; set by admin triage   |

Indexes: `(created_at)`, `(user_id, created_at)`, `(resolved_at)` *(0042)*.

### refresh_tokens *(Phase P)*
One row per minted refresh token — `id` **is** the JWT `jti`. `family_id`
links a rotation chain so replaying an already-rotated token revokes the
whole lineage (reuse detection). Access tokens stay stateless; only refresh
tokens are tracked. Pre-0043 tokens have no `jti` claim and bootstrap into
a new family on first refresh — no backfill needed.

| column         | type              | notes                                              |
|----------------|-------------------|----------------------------------------------------|
| id             | uuid PK           | == JWT `jti`                                       |
| family_id      | uuid              | indexed; rotation chain                            |
| principal_type | varchar(16)       | `user` \| `admin` — mirrors the JWT `pt` claim     |
| subject_id     | uuid              | indexed; users.id or admin_users.id (no FK)        |
| expires_at     | timestamptz       |                                                    |
| revoked_at     | timestamptz NULL  |                                                    |
| revoked_reason | varchar(32) NULL  | `rotated` \| `logout` \| `reuse_detected`          |
| created_at     | timestamptz       |                                                    |

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

### portfolios *(Phase 3 shape)*
| column             | type      | notes                                    |
|--------------------|-----------|------------------------------------------|
| id                 | uuid PK   |                                          |
| user_id            | uuid FK   |                                          |
| title              | text      | renamed from `name`                      |
| short_description  | text NULL | one-liner for cards                      |
| long_description   | text      | renamed from `description`               |
| role               | text NULL | freelancer's role on the project         |
| business_domain    | text NULL | replaces the Phase-1 `business_domains[]`|
| github_url         | text NULL |                                          |
| live_url           | text NULL |                                          |
| technologies       | jsonb     | list[string]                             |
| skills             | jsonb     | list[string]                             |
| features           | jsonb     | list[string]                             |
| outcomes           | jsonb     | list[string]                             |
| highlight          | bool      |                                          |

### opportunity_scores *(Phase 2)*
See [`docs/ROADMAP.md`](ROADMAP.md) Phase 2; one row per job, upserted by
`/jobs/{id}/analyze`.

### resumes *(Phase 4 shape)*
| column              | type      | notes                                   |
|---------------------|-----------|-----------------------------------------|
| id                  | uuid PK   |                                         |
| user_id             | uuid FK   |                                         |
| title               | text      | renamed from `label`                    |
| target_role         | text NULL | "AI / Backend Engineer", etc.           |
| summary             | text NULL | one-paragraph profile blurb             |
| seniority_level     | text NULL | junior / mid / senior / lead / staff /  |
|                     |           | principal                               |
| primary_skills      | jsonb     | list[string] — weight 1.0 in matching   |
| secondary_skills    | jsonb     | list[string] — weight 0.5 in matching   |
| industries          | jsonb     | list[string]                            |
| domains             | jsonb     | list[string] — matched against the job  |
|                     |           | analysis's business_domain              |
| achievements        | jsonb     | list[string]                            |
| project_highlights  | jsonb     | list[string]                            |
| keywords            | jsonb     | list[string]                            |
| notes               | text NULL | private guidance ("when to lead with…") |

Phase 4 dropped the Phase-1 `content`, `file_url`, and `is_default` columns —
the resume is a structured profile, not a file, and recommendations replace
the "default resume" rule.

### skills *(master list)*
| column | type | notes |
|--------|------|-------|
| id     | uuid PK | |
| name   | text UNIQUE | normalized lowercase |
| kind   | enum(technical, domain, soft) | |

### jobs_skills *(m2m)*  ·  portfolio_skills *(m2m)*  ·  resume_skills *(m2m)*
`(parent_id, skill_id, weight numeric)`

### applications *(Phase 6 shape)*
| column              | type      | notes                                                |
|---------------------|-----------|------------------------------------------------------|
| id                  | uuid PK   |                                                      |
| user_id             | uuid FK   |                                                      |
| job_id              | uuid FK   |                                                      |
| proposal_id         | uuid FK NULL |                                                   |
| resume_id           | uuid FK NULL |                                                   |
| portfolio_ids       | jsonb     | list[uuid] copied from the proposal at apply time     |
| status              | enum      | draft, applied, viewed, interview, offer, won,        |
|                     |           | rejected, withdrawn, completed                       |
| applied_at          | timestamptz NULL | set when status first enters `applied`          |
| viewed_at           | timestamptz NULL |                                                |
| interview_at        | timestamptz NULL |                                                |
| offer_at            | timestamptz NULL |                                                |
| won_at              | timestamptz NULL |                                                |
| rejected_at         | timestamptz NULL |                                                |
| withdrawn_at        | timestamptz NULL |                                                |
| completed_at        | timestamptz NULL |                                                |
| contract_amount     | numeric NULL | replaces the Phase-1 `bid_amount`                 |
| client_response     | text NULL |                                                      |
| rejection_reason    | text NULL |                                                      |
| notes               | text NULL |                                                      |
| snapshot            | jsonb NULL | immutable record of job + score + proposal + resume |
|                     |           | + portfolio at submission time                       |

Phase 6 dropped `connects_spent`, `bid_amount`, and `outcome_at` from Phase 1.

### application_history *(Phase 6 shape)*
Append-only log of status transitions on an application.

| column         | type        | notes                                       |
|----------------|-------------|---------------------------------------------|
| id             | uuid PK     |                                             |
| application_id | uuid FK     |                                             |
| user_id        | uuid FK NULL | added in Phase 6                            |
| from_status    | text NULL   | null on the initial create row              |
| to_status      | text        |                                             |
| note           | text NULL   |                                             |
| created_at     | timestamptz | renamed from `changed_at`                   |

### proposals *(Phase 5 shape)*
| column             | type      | notes                                           |
|--------------------|-----------|-------------------------------------------------|
| id                 | uuid PK   |                                                 |
| user_id            | uuid FK   |                                                 |
| job_id             | uuid FK   |                                                 |
| resume_id          | uuid FK NULL | resume used as positioning input             |
| portfolio_ids      | jsonb     | list[uuid] of portfolios referenced in the body |
| title              | text NULL | proposal headline / opening sentence             |
| body               | text      | current text (user-editable)                    |
| short_body         | text NULL | 120–180 word condensed version                  |
| questions          | jsonb     | list[string] — clarifying questions             |
| milestones         | jsonb     | list[{name, description, estimated_hours}]      |
| delivery_approach  | jsonb     | list[string] — 3–5 short steps                  |
| risk_notes         | jsonb     | list[string]                                    |
| quality_score      | int NULL  | 0..100 from the deterministic review            |
| quality_breakdown  | jsonb NULL| per-dimension scores (sum = quality_score)      |
| quality_warnings   | jsonb     | list[string] surfaced by the review             |
| prompt_version     | text NULL | "proposal-v1" etc — for audit                   |
| model_provider     | text NULL | renamed from `provider`                         |
| model_name         | text NULL | renamed from `model`                            |
| raw_response       | jsonb NULL| full provider response for debugging            |

Phase 5 dropped the Phase-1 `draft_body` and numeric `score` columns; the
structured `quality_score` + `quality_breakdown` + `quality_warnings`
replace the single-number self-evaluation.

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

- Phase 1 creates every table in the baseline migration.
- Phase 2 (migration `0002_phase2_analysis_scoring`) extends `job_analyses` with
  structured fields and creates `opportunity_scores`.
- Phase 3 (migration `0003_phase3_portfolio`) reshapes `portfolios` and
  populates `embeddings` with `owner_type ∈ {'portfolio','job'}` rows.
- Phase 4 (migration `0004_phase4_resume`) reshapes `resumes` to the
  structured-profile contract and adds `owner_type='resume'` to `embeddings`.
- Phase 5 (migration `0005_phase5_proposal`) reshapes `proposals` to carry
  the structured proposal body + quality review.
- Phase 6 (migration `0006_phase6_application`) extends `applications` with
  per-status timestamps + immutable snapshot, and adds `draft`/`offer` to
  the status enum.
- Phase K (migration `0028_phase_k_student_persona`) creates
  `student_profiles` + `student_profile_entries` and
  `users.selected_persona_kind`; follow-ups: `0029` adds `department`,
  `0032` adds `date_of_birth`, `0038` backfills every existing user to
  `selected_persona_kind = 'student'` (Careero ships student-only).
- Phase L: `0030` creates `usage_events`, `0031` creates `admin_users`,
  `0033` creates `cv_templates` + `student_profiles.cv_template_slug` and
  seeds the 5 launch templates.
- Phase M: `0034` creates `feedback_entries`; `0042` adds `resolved_at`
  + its index for admin triage.
- Phase N: `0035` adds `photo_offset_x` / `photo_offset_y` / `photo_zoom`
  to `student_profiles`.
- Phase O: `0036` adds `student_profiles.career_pack` JSONB; `0037` /
  `0039` / `0041` add `career_pack.*`, `cv.docx`, and `coach.internship`
  to `usage_event_kind`; `0040` adds `internship` to `student_entry_kind`.
- Phase P: `0043` creates `refresh_tokens`.
