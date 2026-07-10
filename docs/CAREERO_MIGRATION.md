# Careero migration runbook — retiring the `freelance-copilot` identifiers

**Status:** repo-side work landed; GCP + GitHub steps pending an operator with
credentials (Khaled).

The product pivoted to **Careero** but the infrastructure still carries the
pre-pivot name. This runbook retires it. It is a *cutover*, not a find/replace:
Cloud Run services, Cloud SQL instances, GCS buckets, and Artifact Registry
repositories **cannot be renamed in place** — each is create-new → migrate →
verify → delete-old.

Target infrastructure prefix: `careero`.

---

## Decision: GCP project ID stays

**Option A (chosen).** GCP project IDs are **permanently immutable** — Google
does not allow renaming one, ever. The project keeps the ID
`freelance-copilot-841590`; only the *resources inside it* are renamed.

Option B (new project `careero-xxxxx` + full migration) was rejected: it forces
re-issuing every secret, IAM binding, domain mapping, and the Cloud SQL data
migration, for a string nobody outside the GCP console ever sees. Revisit only
if the project must be transferred to a different billing account or org.

The project ID therefore remains in `cloudbuild.yaml` (as the `_PROJECT_ID`
substitution) and in the deployment docs. That is expected, not drift.

---

## Already done in the repo (safe before cutover)

These landed ahead of the infrastructure work and are **backward-compatible** —
they work against the old resources *and* the new ones:

| Change | Why it is safe now |
| --- | --- |
| `apiClient.ts` `*.run.app` host swap is now token-based (`(^\|-)frontend` → `backend`) instead of hardcoding `freelance-copilot-frontend` | Resolves correctly for both `freelance-copilot-frontend-*` and `careero-frontend-*` hosts. Verified against 8 hostnames incl. near-misses (`storefrontend-*` untouched). |
| `cloudbuild.yaml` (frontend + marketing) now take `_PROJECT_ID` / `_ARTIFACT_REPO` substitutions | Defaults are the **current** values, so builds keep working. Cutover is a one-line default change (step 2). |
| `VITE_API_BASE_URL` build-arg is a substitution defaulting to `https://api.careero.app/api/v1` | Removes the previously hardcoded hashed `*.run.app` URL, which rots whenever the service is recreated. |
| User-Agent strings → `careero-scanner/1`, `careero-research/1` | Outbound-only; no system keys off them. |

### Explicitly NOT renamed (traps)

- **`PersonaArmory` / `persona-armory-admin-auth`** — *not* legacy branding.
  PersonaArmory is the live company + admin-surface brand ("Careero is a
  PersonaArmory product"). The storage key is frozen: changing it logs out
  every admin. Leave both alone.
- **`upwork` / `upwork_intel`** (Postgres user + database name) and
  **`upwork-intel-auth`** (frozen student storage key) — the storage key must
  never change; the DB names move only as part of step 6, never as a string edit.
- **Alembic migrations, table names, and columns** — untouched. No migration in
  this runbook alters schema.

---

## Cutover sequence

Run in order. Each step ends in a verification gate; do not proceed past a
failing gate. Steps 2–7 are performed by an operator with `gcloud` access.

### 1. GitHub — rename the repository

Lowest risk; GitHub permanently redirects the old URL, so clones and remotes
keep working.

```bash
gh repo rename careero --repo KSMozn/freelance-copilot
# Contributors update their remote (optional — the redirect works):
git remote set-url origin https://github.com/KSMozn/careero
```

Then update any repo URL still written out in docs. `CONTRIBUTING.md` already
uses a placeholder (`git clone <repo-url>` / `cd <repo-dir>`), so nothing there
needs to change.

**Gate:** `git fetch` succeeds from a fresh clone of the new URL.

### 2. Artifact Registry — new repository

```bash
gcloud artifacts repositories create careero \
  --repository-format=docker \
  --location=europe-west1 \
  --project=freelance-copilot-841590
```

Then flip the default in **both** `frontend/cloudbuild.yaml` and
`marketing/cloudbuild.yaml`:

```yaml
_ARTIFACT_REPO: careero   # was: freelance-copilot
```

Backend images are built by the ad-hoc `gcloud builds submit --tag` command in
`README_DEVELOPMENT_PROCESS.md` — update that tag path in the same change.

**Gate:** one build of each image pushes successfully to
`europe-west1-docker.pkg.dev/freelance-copilot-841590/careero/...`.

### 3. Cloud Run — new services (cannot be renamed)

Deploy `careero-backend` and `careero-frontend` **alongside** the old ones, from
the images now in the `careero` registry. Copy every env var, secret binding,
service account, VPC connector, and Cloud SQL connection from the old service:

```bash
# Inspect the old service and reuse its config verbatim.
gcloud run services describe freelance-copilot-backend \
  --region=europe-west1 --project=freelance-copilot-841590 --format=export > /tmp/backend.yaml
# Edit metadata.name -> careero-backend, then:
gcloud run services replace /tmp/backend.yaml \
  --region=europe-west1 --project=freelance-copilot-841590
```

Repeat for the frontend, and recreate the two jobs:

- `freelance-copilot-migrate` → `careero-migrate`
- `freelance-copilot-promote-superuser` → `careero-promote-superuser`

**Gate:** hit the new services on their raw `*.run.app` URLs.
`https://careero-frontend-<hash>-ew.a.run.app` must resolve its API base to
`https://careero-backend-<hash>-ew.a.run.app/api/v1` — this is exactly what the
token-based swap in `apiClient.ts` now handles. Confirm login works there
**before** touching DNS.

### 4. Domain mappings — move traffic

Move `app.careero.app`, `admin.careero.app`, `api.careero.app` (and the
`*.personaarmory.com` equivalents) from the old services to the new ones.
Domain mappings cannot point at two services at once, so this is the
user-visible moment. Do it in a low-traffic window.

**Gate:** the full smoke checklist below passes against the real domains.

### 5. GCS bucket

Bucket names are global and immutable.

```bash
gcloud storage buckets create gs://careero-uploads \
  --location=europe-west1 --project=freelance-copilot-841590
gcloud storage rsync -r gs://freelance-copilot-841590-uploads gs://careero-uploads
```

Update `GCS_BUCKET` (see `backend/app/core/config.py`) on the new Cloud Run
services, redeploy, then re-run the rsync to catch objects written during the
window.

**Gate:** upload a student photo through the wizard and read it back; confirm
the object lands in `gs://careero-uploads`.

### 6. Cloud SQL — new instance

The riskiest step; it is the only one with irreplaceable state. Cloud SQL
instances cannot be renamed, and an instance name is reserved for ~7 days after
deletion.

1. Create `careero-db` (**match the old instance's Postgres major version** —
   confirm it first: `gcloud sql instances describe freelance-copilot-db
   --format='value(databaseVersion)'`; local dev runs Postgres 16).
2. Enable the `citext` and `vector` extensions — the schema depends on both.
3. Export → import, or use a Database Migration Service job for near-zero
   downtime.
4. Point the new Cloud Run services + `careero-migrate` job at the new instance.
5. Run `alembic upgrade head` against it; the history is linear with a single
   head, so it should be a no-op on a freshly-imported database.

**Gate:** row counts match on `users`, `student_profiles`,
`student_profile_entries`, `refresh_tokens`, and `admin_users`; a real student
signs in and sees their existing CV data. **Keep the old instance until this has
held for at least one full business day.**

### 7. Decommission

Only after every gate above has passed and the new stack has served production
traffic for a full day:

```bash
gcloud run services delete freelance-copilot-frontend --region=europe-west1
gcloud run services delete freelance-copilot-backend  --region=europe-west1
gcloud run jobs delete freelance-copilot-migrate      --region=europe-west1
gcloud run jobs delete freelance-copilot-promote-superuser --region=europe-west1
gcloud artifacts repositories delete freelance-copilot --location=europe-west1
gcloud sql instances delete freelance-copilot-db       # LAST. Take a final export first.
gcloud storage rm -r gs://freelance-copilot-841590-uploads
```

Then update the deployment docs (`README_DEVELOPMENT_PROCESS.md`,
`.github/RELEASE_CHECKLIST.md`, root `CLAUDE.md`) to the `careero-*` names, so
the copy-pasteable `gcloud` commands keep matching reality.

**Rollback at any point before step 7:** the old services, bucket, and database
are still live and untouched. Move the domain mappings back and revert the
`_ARTIFACT_REPO` default. Nothing in steps 1–6 mutates the old stack.

---

## Post-migration validation

Local (must pass before any deploy):

```bash
cd backend  && uv run ruff check . && uv run pytest -q && uv run mypy app
cd frontend && npm run lint && npm run typecheck && npm run build
cd marketing && npm run build
docker compose build
cd frontend && npx playwright test        # needs `make up`
```

Against the deployed Careero stack:

- [ ] `careero-frontend` deployed and serving
- [ ] `careero-backend` deployed and serving
- [ ] Password login + registration
- [ ] OTP request → verify (real email provider in prod)
- [ ] Forgot-password → reset link → old sessions revoked
- [ ] Admin login (separate identity space; user tokens rejected)
- [ ] Student wizard: all 13 steps, autosave, CV preview, PDF + DOCX download
- [ ] Photo upload lands in `gs://careero-uploads`
- [ ] Impersonation: admin → student, fragment decoded and wiped
- [ ] `careero-migrate` job runs `alembic upgrade head` cleanly
- [ ] Daily-report task endpoint still authenticates via `X-Task-Secret`
- [ ] Old services removed, and nothing 404s

---

## Definition of done

No `freelance-copilot` string remains in the repo except:

- the immutable GCP **project ID** `freelance-copilot-841590`;
- historical references in `docs/ROADMAP.md` and git history.

Everything else — services, jobs, registry, bucket, database, repo — is
`careero`.
