# CLAUDE.md — AI Development Guide for the Freelance Copilot Frontend

## Project Overview

**Freelance Copilot Frontend** is a single-repo React 18 + TypeScript SPA built with Vite. One build serves **three surfaces**, selected at runtime from the hostname (or a sticky `?surface=` override): the **Careero** student CV builder (`app.*`), the **PersonaArmory Admin** console (`admin.*`), and a **dormant professional Career-OS surface** whose routes are intentionally not registered.

Bundled features:

- **`features/auth`** — foundation feature. Student OTP login/registration (`POST /auth/request-code` → `verify-code`), password fallback, the admin↔app **impersonation bridge** (`ImpersonateLandingPage` decodes a URL-fragment token payload, stores it, wipes the fragment), `RequireAuth` route gate, and the Zustand auth stores (`authStore`, `lastProfileStore`).
- **`features/student-wizard`** — the live product: a 13-step CV wizard (profile autosave + explicit-save entry steps), photo cropping, CV preview/PDF/DOCX export, and three **nested** sub-modules it owns: `coaching/`, `career-pack/`, `feedback/`. **Do NOT extract these into sibling features** — they depend on student-profile ownership (career-pack imports `useUpdateStudentProfile`).
- **`features/admin`** — flat bounded feature: password login (`adminAuthStore`), users/feedback/emails/templates/activity pages, LLM spend tracking, impersonation sender. **Do NOT split it by page** — `adminApi.ts` stays one file because its ~25 hooks share TanStack query keys and broad `["admin"]` invalidations.
- **`features/professional`** — the dormant Career-OS (jobs, analysis, proposals, portfolio, resumes, repositories, applications, analytics, personas, sources, outputs, shell). **DO NOT delete it, DO NOT register its routes, DO NOT import it from live code.** The quarantine is ESLint-enforced in both directions.

> **Package manager:** npm (`package-lock.json` is the source of truth). Never commit a `yarn.lock`.

---

## Tech Stack

- **Framework**: React 18 + TypeScript 5.7
- **Build**: Vite 6 (with `@vitejs/plugin-react`)
- **Styling**: Tailwind CSS v3 — config-based tokens (`tailwind.config.js`); shadcn-style HSL variables + brand-gradient utilities in `src/shared/styles/globals.css`
- **Components**: hand-rolled shadcn-style primitives in `src/shared/ui/`, on **Base UI** (`@base-ui/react`) where a primitive exists (Button), styled with CVA (`class-variance-authority`)
- **Utilities**: `clsx` + `tailwind-merge` (via `cn()` from `@/shared/lib/utils`)
- **Icons**: `lucide-react`
- **Notifications**: `toast` from `sonner`
- **Server state**: **TanStack Query** (`useQuery`, `useMutation`, `invalidateQueries`, `setQueryData`)
- **Client state**: **Zustand** with `persist` middleware — storage keys are **frozen** (see Security Note)
- **HTTP**: axios via the single client in `src/app/apiClient.ts`
- **Routing**: `react-router-dom` v6, `<BrowserRouter>` + eager `<Routes>` JSX in `src/app/router.tsx`
- **Validation**: `zod` — the standard for **new** schemas (existing hand-rolled validation is not being rewritten wholesale)
- **Formatting**: Prettier (`printWidth: 100`, `prettier-plugin-tailwindcss`)
- **Linting**: ESLint 9 (flat config) with `eslint-plugin-import-x` layer boundaries
- **Git hooks**: Husky + lint-staged (pre-commit: eslint --fix + prettier on staged frontend files; no pre-push hook by design)
- **Storybook**: v10 (react-vite) for `src/shared/ui/` components

### 🚫 Forbidden — state management

**NO REDUX. Never.** Do not add, suggest, or migrate toward `redux`, `react-redux`, `@reduxjs/toolkit`, or RTK Query. Do not replace TanStack Query or Zustand. Server state belongs in TanStack Query; client state in Zustand.

---

## Mental Model

| Surface          | Host / trigger                        | What renders                              |
| ---------------- | ------------------------------------- | ----------------------------------------- |
| **Student app**  | `app.*` hosts (default)               | Careero CV wizard (`AppRoutes`)           |
| **Admin**        | `admin.*` hosts or sticky `?surface=admin` | PersonaArmory console (`AdminRoutes`) |
| **Professional** | — (routes not registered)             | Nothing. Dormant by design.               |

| Layer         | Location         | Purpose                                                        |
| ------------- | ---------------- | -------------------------------------------------------------- |
| **app**       | `src/app/`       | Bootstrap wiring: axios client, query client, router/surfaces. **No business logic.** |
| **features**  | `src/features/`  | All product code, one folder per bounded feature               |
| **shared**    | `src/shared/`    | Sink: ui primitives, brand config, hooks, `cn()`, styles       |

---

## Repository Map

```
src/
├── main.tsx                     # StrictMode > QueryClientProvider > BrowserRouter > AppRouter + Toaster
├── app/                         # LAYER: wiring
│   ├── apiClient.ts             # axios instance + interceptors + isAdminSurface + logoutCurrentSurface
│   ├── queryClient.ts           # TanStack QueryClient singleton
│   └── router.tsx               # AppRouter: isAdminSurface ? AdminRoutes : AppRoutes
│
├── features/
│   ├── auth/                    # Foundation — flat, one file per concern
│   │   ├── authStore.ts         # Zustand+persist ("upwork-intel-auth" — FROZEN)
│   │   ├── lastProfileStore.ts  # Login-picker snapshot ("careero-last-profile" — FROZEN)
│   │   ├── RequireAuth.tsx · LoginPage · RegisterPage · OnboardingPage
│   │   └── ImpersonateLandingPage.tsx   # fragment decode → setAuth → wipe → /student
│   │
│   ├── student-wizard/
│   │   ├── StudentWizardPage.tsx  # STEPS config, ProgressBar, StepBody dispatch, save-model captions
│   │   ├── steps/                 # one file per wizard step (+ EntryForm, InternshipCard, wizardShared)
│   │   ├── studentApi.ts · studentTypes.ts · studentSuggestions.ts · photoCache.ts
│   │   ├── PhotoPositioner.tsx · DateOfBirthPicker.tsx · data/
│   │   ├── coaching/              # coachingApi (6 AI hooks) · coachingTypes · CoachWarnings
│   │   ├── career-pack/           # CareerStarterPack · careerPackApi · careerPackTypes
│   │   └── feedback/              # StudentFeedbackPage · PostDownloadSurvey · feedbackApi · feedbackTypes
│   │
│   ├── admin/                   # Flat bounded feature — do not split by page
│   │   ├── adminApi.ts          # ALL admin TanStack hooks — keep together (shared keys/invalidations)
│   │   ├── adminAuthStore.ts    # Zustand+persist ("persona-armory-admin-auth" — FROZEN)
│   │   ├── adminTypes.ts        # types + defensive parsers (parseInternshipAuditDetails)
│   │   └── AdminLayout · AdminLoginPage · Admin{Overview,Users,UserDetail,Feedback,Emails,Templates,Activity}Page · LlmSpendCard
│   │
│   └── professional/            # DORMANT Career-OS — quarantined, unrouted
│       ├── apiTypes.ts + shell/ dashboard/ jobs/ analysis/ proposals/ portfolio/
│       └── resumes/ repositories/ applications/ analytics/ career-fitness/ sources/ outputs/ personas/
│
└── shared/                      # LAYER: sink — no imports from app/ or features/
    ├── ui/                      # button, badge, card, combobox, input, label, select, textarea (+ *.stories.tsx) + brand/
    ├── config/brand.ts          # BRAND names/taglines + STORAGE_KEYS (frozen)
    ├── hooks/useAutoSave.ts · lib/utils.ts (cn) · styles/globals.css
```

### Layered dependency DAG (enforced by ESLint)

```
shared        ← sink (external imports + sibling shared only)
  ↑
app           (may import features + shared; owns bootstrap/routing/surface selection)
  ↑
features/auth            foundation — no imports from other features
features/student-wizard  owns coaching/ career-pack/ feedback/ internally
features/admin           isolated flat feature
features/professional    DORMANT — nothing outside it may import it, and it
                         may not import student-wizard or admin
```

Enforced rules (see `eslint.config.js` → `import-x/no-restricted-paths`):

- `shared/*` may not import from `app/` or `features/*` — it is a sink.
- `features/auth` may not import from any other feature.
- **Nothing** in `app/`, `student-wizard`, or `admin` may import `features/professional` (enforced dormancy), and `professional` may not import the live features.
- No barrel imports of the shape `@/features/*/index` — import the concrete file.

When you add a new domain feature, add a zone under `import-x/no-restricted-paths` to keep it isolated from its peers.

---

## Path Aliases

| Alias | Resolves to | Use for               | Example                                                |
| ----- | ----------- | --------------------- | ------------------------------------------------------ |
| `@/`  | `./src/`    | ALL internal imports  | `import { Button } from "@/shared/ui/button"`          |

There is **no** `@lib` alias and no design-system barrel — import concrete files. Sibling imports (`./steps/StepBasics`) are fine within a feature; **never** use `../../../` relative paths across folders.

---

## Key Commands

```bash
npm install              # Install deps (also activates husky via prepare)
npm run dev              # App → localhost:5173
npm run storybook        # Component browser → localhost:6006
npm run build            # Type-check + build → dist/
npm run preview          # Preview the built app
npm run lint             # ESLint (check only — lint-staged does the fixing)
npm run format           # Prettier --write over src
npm run format:check     # Prettier --check over src
npm run typecheck        # tsc --noEmit
npm run build-storybook  # Static Storybook → storybook-static/
npm run clean            # Remove node_modules/dist/etc (NEVER touches package-lock.json)
```

---

## Environment variables & surface selection

Copy `.env.example` → `.env` if needed:

| Var                 | Purpose                                          | Default                        |
| ------------------- | ------------------------------------------------ | ------------------------------ |
| `VITE_API_BASE_URL` | Dev fallback API base for `src/app/apiClient.ts` | `http://localhost:8000/api/v1` |

In deployed environments the API base is resolved **at runtime from the hostname** (`*.careero.app` → `api.careero.app`, `*.personaarmory.com` → `api.personaarmory.com`, `*.run.app` → paired Cloud Run backend). The admin surface is picked the same way (`admin.*` hosts) with a sticky `?surface=admin` sessionStorage override for raw Cloud Run URLs; `?surface=app` clears it. This logic lives in `apiClient.ts` and runs at module load — do not duplicate or reorder it.

---

## API & Server-State Rules

`src/app/apiClient.ts` is the **only** axios client. It owns, and you must preserve:

- Bearer-token injection from the surface-appropriate Zustand store
- the single-flight 401 refresh (`refreshInFlight`) with retry-once semantics
- `logoutCurrentSurface()` (best-effort server-side refresh-token revocation)
- `isAdminSurface` computed at module load

Do **not** create additional axios instances or fetch wrappers. Per-feature data access lives in the feature's `<name>Api.ts` as hand-written TanStack Query hooks (`useXQuery`/`useXMutation` style) importing `api` from `@/app/apiClient`. Query keys are hierarchical per feature (`["admin", ...]`, `["student", ...]`) — mutations invalidate by prefix; keep new keys inside the feature's hierarchy.

---

## How to Add a Feature

1. Create `src/features/<name>/` — keep it flat, one file per concern:

   ```
   features/<name>/
   ├── <Name>Page.tsx             # thin page component(s)
   ├── <name>Api.ts               # TanStack Query hooks over @/app/apiClient
   ├── <name>Types.ts             # TS domain types (+ defensive parsers for untyped blobs)
   ├── <name>Schema.ts            # zod schemas (required for NEW validation)
   ├── <name>Store.ts             # Zustand store ONLY if real client state exists
   └── use<Name>.ts               # feature hooks (if needed)
   ```

2. Register the route in `src/app/router.tsx` — **in the correct surface tree** (`AppRoutes` vs `AdminRoutes`), wrapping in `<RequireAuth>` (app) or relying on `AdminLayout`'s guard (admin). Never register anything from `features/professional`.

3. Add a zone to `eslint.config.js` → `import-x/no-restricted-paths` to keep the feature isolated from its peers.

4. Keep pages thin; lift data hooks into `<name>Api.ts`. If the feature persists client state, the storage key must be added to `STORAGE_KEYS` in `@/shared/config/brand.ts` and never changed afterwards.

Reference: `src/features/admin/` is the canonical flat feature; `src/features/student-wizard/` shows nested sub-modules a feature may own.

---

## How to Add a Component (in `src/shared/ui/`)

1. Create `src/shared/ui/<name>.tsx` (lowercase shadcn-style filename) and `<name>.stories.tsx` — **stories are required** for shared/ui components.

2. Component pattern:

   ```tsx
   import { SomePrimitive } from "@base-ui/react/some-primitive"; // if Base UI has one
   import { cva, type VariantProps } from "class-variance-authority";

   import { cn } from "@/shared/lib/utils";

   const myVariants = cva("base-classes", {
     variants: { /* ... */ },
     defaultVariants: { /* ... */ },
   });

   export const MyComponent = React.forwardRef<HTMLElement, Props>(
     ({ className, variant, ...props }, ref) => (
       <SomePrimitive ref={ref} className={cn(myVariants({ variant, className }))} {...props} />
     ),
   );
   MyComponent.displayName = "MyComponent";
   ```

3. **Base UI first** for primitives that exist (`@base-ui/react/<primitive>` subpath imports); plain elements otherwise (Label is a plain `<label>`). Never reintroduce Radix.

4. Preserve existing component APIs — e.g. `Button`'s `asChild` prop is public API (mapped internally to Base UI's `render` prop) and must keep working.

---

## Theming

Design tokens are shadcn-style HSL CSS variables in `src/shared/styles/globals.css` (`:root` + `.dark` blocks) bridged into Tailwind via `tailwind.config.js` — **Tailwind v3 config-based, not v4 CSS-first**. Brand gradient utilities (`bg-brand-gradient`, `text-brand-gradient`, …) live in the same file. There is **no runtime theme-toggle system** — do not add one casually.

Brand strings (Careero / PersonaArmory names + taglines) come from `@/shared/config/brand.ts` — never hardcode them in new code.

---

## Code Quality Gates

### Pre-commit (lint-staged — runs via `frontend/.husky/pre-commit`)

- `src/**/*.{ts,tsx}` → `eslint --quiet --fix`
- `src/**/*.{ts,tsx,css}` → `prettier --write`

The git root is the repo root; hooks `cd frontend` first. Backend-only commits pass through instantly. There is **no pre-push hook** (deliberate — do not add a branch blocker without being asked).

### ESLint rules (highlights)

- Layer-boundary zones via `import-x/no-restricted-paths` (the DAG above) — **never remove these**
- Feature-barrel imports banned
- `@typescript-eslint/no-unused-vars` → error (underscore prefix to ignore)
- React hooks rules enforced; `react-refresh/only-export-components` (off for `*.stories.tsx`)

---

## After Every Code Change

Always run before handing off — no exceptions:

```bash
npm run format && npm run lint && npm run typecheck
```

---

## Docker / running the full stack

Two images live here: `Dockerfile` (dev — used by the repo-root `docker-compose.yml`, bind-mounts the source and runs `npm run dev`) and `Dockerfile.prod` (Cloud Run — `npm ci` → `tsc -b && vite build` → nginx-unprivileged, built via `cloudbuild.yaml`). Neither runs ESLint; typecheck happens in the prod build via `tsc -b`. The full local stack (Postgres + FastAPI backend + this frontend) runs from the repo root: `make up`, `make migrate`, `make create-admin` (see the root `Makefile`).

---

## Security Note — Token & storage keys

Auth tokens (access + refresh) persist via Zustand `persist` in `localStorage` under **frozen keys** — `upwork-intel-auth`, `persona-armory-admin-auth`, `careero-last-profile` (centralized in `STORAGE_KEYS`, `@/shared/config/brand.ts`). **Changing any key value logs every existing user out.** The impersonation bridge passes tokens in a URL **fragment** (never sent to a server) and wipes it on landing — preserve that contract exactly. For production hardening, HttpOnly cookies would mitigate XSS token exfiltration; track separately, don't improvise.

---

## Coding Conventions

- **Imports**: `@/` for everything internal; concrete files, no barrels; sibling `./` only within a feature folder.
- **Components**: PascalCase component names; pages suffixed `Page`; non-component feature modules camelCase with feature prefix (`adminApi.ts`, `studentTypes.ts`).
- **Exports**: Named exports only — no `export default` (Storybook meta is the sole exception).
- **Styling**: `cn()` to merge conditional Tailwind classes; CVA for variant systems; tokens over hex.
- **Icons**: `lucide-react`. **Notifications**: `toast` from `sonner`.
- **Validation**: zod for new schemas, co-located with their feature (`<name>Schema.ts`); truly cross-cutting types go in `src/shared/types/` (create it when first needed).
- **No `any`** — untyped JSONB blobs get typed parsers (see `parseInternshipAuditDetails`).
- **`displayName`** on every shared/ui component; **stories** for every shared/ui component.
- **No `console.log`** left in committed code.
- The wizard's **two save models are intentional** (profile steps autosave; entry/internship steps save explicitly) — the footer captions in `StudentWizardPage.tsx` must stay truthful to `SAVE_MODEL`. Do not unify the models.

---

## Branching Workflow

- `main` — default branch; work lands via feature branches + PRs (`refactor/`, `feat/`, `fix/` prefixes in use)
- No push blockers are installed — keep it that way unless asked.

---

## Historical note

This frontend was migrated (2026-07) from a type-sorted layout (`components/`, `pages/`, `lib/`, `stores/`, `types/`) to the current feature-driven structure, mirroring the reference architecture pattern. Do not reference or recreate the old folders; the migration history lives on the `refactor/feature-driven-frontend` branch.

---

## Hard Rules

- **Never push. Commit only when the developer explicitly asks.** Otherwise validate and prepare.
- **Never add `Co-authored-by`, AI attribution, or agent attribution lines for Claude, Copilot, or any other agent unless the developer explicitly asks.**
- **Always run `format` + `lint` + `typecheck` after any code change.**
- **NO REDUX** — no `redux`, `react-redux`, `@reduxjs/toolkit`, no RTK Query. Never replace TanStack Query or Zustand.
- **Never change persisted storage key values** (`STORAGE_KEYS` is frozen).
- **Never mount, route, or import `features/professional`** — restoring it is a deliberate human decision, not a refactor side-effect.
- **Never extract `coaching/`, `career-pack/`, or `feedback/` out of `features/student-wizard`.**
- **Keep `features/admin` flat and `adminApi.ts` whole.**
- Do not redesign UI, change the architecture, move features, rewrite working logic, replace libraries, or fix unrelated bugs without an explicit request.
- Preserve the multi-surface switching and the impersonation contract byte-for-byte.
- Use `@/` for internal imports — never relative paths across folders, never feature barrels.
- Never use `any`.
- Every `src/shared/ui` component needs a `.stories.tsx` file and a `displayName`.
- Never add dependencies without confirming with the developer.
- Base UI primitives are imported from their specific subpath (e.g. `@base-ui/react/button`) — never reintroduce Radix.
