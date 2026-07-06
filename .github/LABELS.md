# Careero — GitHub Labels

Reference list of the labels we use to triage issues and PRs. Create these once on
the repo (Settings → Labels, or use `gh label create` in a script). At minimum every
issue / PR gets one **type** label and one **area** label.

---

## Type

| Label | Colour | When to use |
|---|---|---|
| `feature` | `#0e8a16` | New user-facing capability. |
| `bug` | `#d73a4a` | Something is broken. Pair with severity if urgent. |
| `chore` | `#c5def5` | Refactor, docs, tooling, dependency bump. No user-visible change. |
| `ui` | `#f9d0c4` | Visual / interaction change only. |
| `ai` | `#8b5cf6` | LLM prompts, coach services, honesty rules. |

## Area

| Label | Colour | When to use |
|---|---|---|
| `frontend` | `#1d76db` | React / Vite / TypeScript changes. |
| `backend` | `#fbca04` | FastAPI / Python / DB changes. |
| `cv-export` | `#0052cc` | CV renderer changes (either PDF or DOCX). |
| `pdf-export` | `#0e4b99` | PDF-specific: WeasyPrint, Jinja templates. |
| `docx-export` | `#5319e7` | DOCX-specific: python-docx renderer. |
| `email-template` | `#e99695` | Admin-triggered or transactional email HTML/txt. |
| `linkedin` | `#0a66c2` | LinkedIn generation / review flow. |
| `github-profile` | `#333333` | GitHub review flow. |
| `internship` | `#00875a` | Internship wizard step, coach, renderer. |
| `admin` | `#666666` | Admin panel changes. |
| `infra` | `#bfd4f2` | Cloud Run, Cloud SQL, secrets, CI. |

## Priority / State

| Label | Colour | When to use |
|---|---|---|
| `urgent` | `#b60205` | Production is down, data loss risk, or students can't complete the wizard. Pair with `hotfix` branch. |
| `good-first-issue` | `#7057ff` | Small, well-scoped issue with clear acceptance criteria. Safe for a new contributor. |
| `needs-review` | `#fbca04` | Issue is filled in and waiting on triage / a PR is waiting on a reviewer. |
| `ready-for-testing` | `#0e8a16` | PR is merged, deployed, awaiting the release checklist. |
| `blocked` | `#e11d48` | Cannot proceed without something external (schema decision, third-party fix, design). Describe the block in a comment. |
| `wontfix` | `#ffffff` | Closed without action; note the reason. |
| `duplicate` | `#cccccc` | Reference the earlier issue in a comment. |

---

## Creation

If you have `gh` installed:

```bash
gh label create feature           --color 0e8a16 --description "New user-facing capability"
gh label create bug               --color d73a4a --description "Something is broken"
gh label create chore             --color c5def5 --description "Refactor, docs, tooling"
gh label create ui                --color f9d0c4 --description "Visual / interaction change"
gh label create ai                --color 8b5cf6 --description "LLM prompts / coach services"

gh label create frontend          --color 1d76db --description "React / Vite / TS"
gh label create backend           --color fbca04 --description "FastAPI / Python / DB"
gh label create cv-export         --color 0052cc --description "CV renderer (PDF or DOCX)"
gh label create pdf-export        --color 0e4b99 --description "PDF-specific"
gh label create docx-export       --color 5319e7 --description "DOCX-specific"
gh label create email-template    --color e99695 --description "Email HTML/txt templates"
gh label create linkedin          --color 0a66c2 --description "LinkedIn coach flow"
gh label create github-profile    --color 333333 --description "GitHub coach flow"
gh label create internship        --color 00875a --description "Internship section"
gh label create admin             --color 666666 --description "Admin panel"
gh label create infra             --color bfd4f2 --description "Cloud Run / SQL / CI"

gh label create urgent            --color b60205 --description "Production incident"
gh label create good-first-issue  --color 7057ff --description "Suitable for a new contributor"
gh label create needs-review      --color fbca04 --description "Awaiting triage or review"
gh label create ready-for-testing --color 0e8a16 --description "Merged, awaiting release checklist"
gh label create blocked           --color e11d48 --description "Waiting on something external"
gh label create wontfix           --color ffffff --description "Closed without action"
gh label create duplicate         --color cccccc --description "Duplicate of another issue"
```

---

## Combining Labels

**A typical feature issue** ends up with something like:

`feature` + `frontend` + `internship` + (later) `needs-review` → `ready-for-testing`

**A CV export bug** would be:

`bug` + `backend` + `cv-export` + `docx-export` + `urgent` (if truly urgent)

**Docs / process change:**

`chore` (no area needed).
