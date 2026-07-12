# CLAUDE.md — Rules for docs/

These documents are **contracts with reality** — they describe the code as it
is, not as it was or might be. Drift here caused a full product-description
mismatch once (README advertising the pre-pivot product); don't repeat it.

## The files

| File | Tracks | Update trigger |
| --- | --- | --- |
| `ARCHITECTURE.md` | Backend layering + subsystem walkthroughs | Any new subsystem, auth change, or layering decision |
| `ERD.md` | Database schema | **Every Alembic migration** — same PR |
| `ROADMAP.md` | Phase history (professional era + Careero era) | Every shipped phase |
| `llm-visibility-playbook.md` | Marketing-site SEO/LLM strategy | Marketing changes |
| `CAREERO_MIGRATION.md` | Cutover runbook retiring the `freelance-copilot` infra names | Each completed migration step |

## Rules

- **Label surfaces**: every section must be attributable to the **live**
  surface (Careero student + PersonaArmory admin) or the **dormant**
  professional surface. Dormant documentation is kept (it documents real,
  running backend code) but must be marked as dormant.
- **ERD.md moves with migrations**: a PR adding migration `00XX` updates
  ERD.md in the same PR. Document: columns, types, nullability, indexes,
  constraints, FKs, enum additions.
- **ROADMAP.md phase sections** follow the established format: goal,
  migrations, services, API, frontend, exit criteria. Only shipped work —
  aspirations go in issues.
- **Verify before writing**: claims cite real files/migrations. If you didn't
  read it in code, don't write it.
- Frontend architecture is documented in `frontend/CLAUDE.md`, backend rules
  in `backend/CLAUDE.md` — link, don't duplicate.
- Never add AI/agent attribution lines; commit only when asked.
