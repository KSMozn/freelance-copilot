"""Scan a GitHub repository and extract structured stack metadata.

Pipeline:
  1. Fetch repo metadata + language byte counts.
  2. Fetch a fixed set of manifest / config files.
  3. Heuristic extraction → frameworks, libraries, dbs, auth, ai, cloud, ci,
     tests, docker (deterministic; no LLM call).
  4. LLM step: feed README excerpt + structured findings to AIProvider and
     ask for `architecture_summary`, `business_domain`, `strengths`,
     `highlights`. Schema-validated; soft-fails (the LLM step is optional).

Result is a plain dict suitable for `RepositoryStore.update(fields=…)`.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.domain.providers.ai_provider import AIProvider
from app.infrastructure.github.github_client import (
    GithubClient,
    GithubError,
    GithubFile,
)

logger = logging.getLogger(__name__)


# --- Files to fetch ---------------------------------------------------------

MANIFEST_PATHS: tuple[str, ...] = (
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "poetry.lock",
    "go.mod",
    "Cargo.toml",
    "Gemfile",
    "composer.json",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
)

CONFIG_PATHS: tuple[str, ...] = (
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "vercel.json",
    "netlify.toml",
    "fly.toml",
    "render.yaml",
    "serverless.yml",
    "next.config.js",
    "next.config.mjs",
    "tsconfig.json",
    "vite.config.ts",
    "vite.config.js",
    ".gitlab-ci.yml",
    "Makefile",
    "README.md",
    "readme.md",
)

# --- Heuristic dictionaries -------------------------------------------------

FRAMEWORK_DEPS: dict[str, list[str]] = {
    "Next.js": ["next"],
    "React": ["react"],
    "Vue": ["vue"],
    "Svelte": ["svelte"],
    "Angular": ["@angular/core"],
    "Express": ["express"],
    "Fastify": ["fastify"],
    "NestJS": ["@nestjs/core"],
    "FastAPI": ["fastapi"],
    "Django": ["django"],
    "Flask": ["flask"],
    "Starlette": ["starlette"],
    "Pyramid": ["pyramid"],
    "Spring Boot": ["spring-boot-starter"],
    "Gin": ["github.com/gin-gonic/gin"],
    "Echo": ["github.com/labstack/echo"],
    "Rails": ["rails"],
    "Laravel": ["laravel/framework"],
    "Actix": ["actix-web"],
    "Axum": ["axum"],
    "tRPC": ["@trpc/server"],
    "GraphQL": ["graphql", "apollo-server"],
}

DATABASE_DEPS: dict[str, list[str]] = {
    "PostgreSQL": ["psycopg", "psycopg2", "asyncpg", "pg", "sqlalchemy", "drizzle-orm", "prisma", "knex", "pq", "github.com/lib/pq"],
    "MySQL": ["mysql", "mysql2", "mysqlclient", "pymysql"],
    "SQLite": ["sqlite3", "better-sqlite3", "aiosqlite"],
    "MongoDB": ["mongoose", "mongodb", "motor", "pymongo"],
    "Redis": ["redis", "ioredis", "aioredis", "@upstash/redis"],
    "Elasticsearch": ["@elastic/elasticsearch", "elasticsearch"],
    "DynamoDB": ["@aws-sdk/client-dynamodb", "boto3"],
    "ClickHouse": ["clickhouse-driver", "@clickhouse/client"],
    "Snowflake": ["snowflake-connector-python"],
    "Pinecone": ["pinecone-client", "@pinecone-database/pinecone"],
    "pgvector": ["pgvector"],
    "Supabase": ["@supabase/supabase-js", "supabase"],
}

AUTH_DEPS: dict[str, list[str]] = {
    "JWT": ["jsonwebtoken", "jose", "pyjwt", "python-jose"],
    "OAuth": ["passport", "next-auth", "@auth/core", "authlib", "oauthlib"],
    "Auth0": ["@auth0/auth0-react", "auth0"],
    "Clerk": ["@clerk/clerk-sdk-node", "@clerk/nextjs", "clerk-sdk-python"],
    "Supabase Auth": ["@supabase/auth-helpers-nextjs"],
    "FastAPI Users": ["fastapi-users"],
    "Passlib / bcrypt": ["passlib", "bcrypt", "argon2", "argon2-cffi"],
}

AI_DEPS: dict[str, list[str]] = {
    "OpenAI": ["openai"],
    "Anthropic": ["anthropic", "@anthropic-ai/sdk"],
    "LangChain": ["langchain", "langchain-core", "@langchain/core"],
    "LlamaIndex": ["llama-index", "llama_index"],
    "Hugging Face": ["transformers", "huggingface_hub", "@huggingface/inference"],
    "Vercel AI SDK": ["ai"],
    "Cohere": ["cohere", "cohere-ai"],
    "Google GenAI": ["google-generativeai"],
}

CLOUD_FILES: dict[str, list[str]] = {
    "AWS": ["serverless.yml", "sam.yaml", "template.yaml"],
    "Vercel": ["vercel.json"],
    "Netlify": ["netlify.toml"],
    "Fly.io": ["fly.toml"],
    "Render": ["render.yaml"],
    "Cloudflare": ["wrangler.toml"],
    "GCP": ["app.yaml", "cloudbuild.yaml"],
    "Azure": ["azure-pipelines.yml", "host.json"],
}

CLOUD_DEPS: dict[str, list[str]] = {
    "AWS": ["@aws-sdk/", "boto3", "aws-cdk-lib", "aws-amplify"],
    "GCP": ["@google-cloud/"],
    "Azure": ["@azure/"],
    "Cloudflare": ["@cloudflare/workers-types", "wrangler"],
    "Vercel": ["@vercel/"],
}

TEST_DEPS: dict[str, list[str]] = {
    "pytest": ["pytest"],
    "Jest": ["jest"],
    "Vitest": ["vitest"],
    "Playwright": ["@playwright/test", "playwright"],
    "Cypress": ["cypress"],
    "Mocha": ["mocha"],
    "Testing Library": ["@testing-library/react", "@testing-library/vue"],
    "unittest": ["unittest2"],
    "Go test": [],  # detected by language presence
    "JUnit": ["junit"],
}


# --- Result ----------------------------------------------------------------


@dataclass(slots=True)
class ScanResult:
    """Dict-of-fields that callers feed into `RepositoryStore.update`.

    Fields exactly match the Repository ORM columns so the service can pass
    `result.as_update_fields()` straight through.
    """

    owner: str
    name: str
    default_branch: str | None
    description: str | None
    languages: dict[str, int]
    frameworks: list[str]
    libraries: list[str]
    databases: list[str]
    authentication: list[str]
    ai_providers: list[str]
    cloud: list[str]
    ci_systems: list[str]
    test_frameworks: list[str]
    has_docker: bool
    has_ci: bool
    has_tests: bool
    readme_excerpt: str | None
    architecture_summary: str | None
    business_domain: str | None
    strengths: list[str]
    highlights: list[str]
    path_index: list[str]

    def as_update_fields(self) -> dict[str, object]:
        return {
            "owner": self.owner,
            "name": self.name,
            "default_branch": self.default_branch,
            "description": self.description,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "libraries": self.libraries,
            "databases": self.databases,
            "authentication": self.authentication,
            "ai_providers": self.ai_providers,
            "cloud": self.cloud,
            "ci_systems": self.ci_systems,
            "test_frameworks": self.test_frameworks,
            "has_docker": self.has_docker,
            "has_ci": self.has_ci,
            "has_tests": self.has_tests,
            "readme_excerpt": self.readme_excerpt,
            "architecture_summary": self.architecture_summary,
            "business_domain": self.business_domain,
            "strengths": self.strengths,
            "highlights": self.highlights,
            "path_index": self.path_index,
            "scan_status": "scanned",
            "scan_error": None,
            "scanned_at": datetime.now(UTC),
        }


# --- LLM schema -------------------------------------------------------------


class _ArchitectureSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    architecture_summary: str = Field(min_length=1, max_length=1200)
    # Truncated downstream — the DB column is VARCHAR(120) and some models
    # ignore "short label" hints and return a paragraph.
    business_domain: str | None = None
    strengths: list[str] = Field(default_factory=list, max_length=8)
    highlights: list[str] = Field(default_factory=list, max_length=8)


_LLM_SYSTEM_PROMPT = (
    "You are an experienced engineering director reviewing a GitHub repository "
    "to extract its technical character for proposal-writing. Read the supplied "
    "README excerpt and structured findings. Reply with strict JSON matching "
    "the requested schema. Never invent technologies or features that are not "
    "evidenced by the input. Keep `architecture_summary` to one tight "
    "paragraph (~3 sentences). `business_domain` MUST be a SHORT label — "
    "1–3 words MAX, like 'AI SaaS', 'Industrial Operations', 'Document "
    "Management'. Do NOT write a sentence in business_domain. `strengths` "
    "and `highlights` should be concrete (e.g. 'Async FastAPI + pgvector "
    "backend', not 'Modern stack')."
)


def _build_llm_prompt(*, scan: ScanResult) -> str:
    return (
        f"Repository: {scan.owner}/{scan.name}\n"
        f"Description: {scan.description or '(none)'}\n"
        f"Languages (bytes): {json.dumps(scan.languages)}\n"
        f"Frameworks: {scan.frameworks}\n"
        f"Libraries: {scan.libraries}\n"
        f"Databases: {scan.databases}\n"
        f"Authentication: {scan.authentication}\n"
        f"AI providers: {scan.ai_providers}\n"
        f"Cloud: {scan.cloud}\n"
        f"CI: {scan.ci_systems}\n"
        f"Tests: {scan.test_frameworks}\n"
        f"Has Docker: {scan.has_docker}\n\n"
        f"README excerpt:\n{scan.readme_excerpt or '(no README)'}"
        "\n\nRespond with JSON: {architecture_summary: str, business_domain: str|null, "
        "strengths: [str], highlights: [str]}"
    )


# --- Scanner ---------------------------------------------------------------


class RepositoryScanService:
    def __init__(
        self,
        *,
        github_client: GithubClient,
        ai_provider: AIProvider,
    ) -> None:
        self._gh = github_client
        self._ai = ai_provider

    async def scan(self, *, owner: str, name: str) -> ScanResult:
        meta = await self._gh.get_repo(owner, name)
        files = await self._fetch_files(
            owner=meta.owner,
            name=meta.name,
            ref=meta.default_branch,
            languages=meta.languages,
        )
        try:
            workflows = await self._gh.list_dir(
                meta.owner, meta.name, ".github/workflows", ref=meta.default_branch
            )
        except GithubError as exc:
            logger.warning("scanner: workflows dir fetch failed: %s", exc)
            workflows = []

        try:
            tree_entries = await self._gh.get_tree(
                meta.owner, meta.name, sha=meta.default_branch, recursive=True
            )
        except GithubError as exc:
            logger.warning("scanner: tree fetch failed: %s", exc)
            tree_entries = []
        path_index = _build_path_index(tree_entries)

        # Monorepo support: if the root package.json declares `workspaces`,
        # resolve each pattern against the tree and fetch the workspace
        # package.json files so their deps land in the heuristic dictionary.
        root_pkg = files.get("package.json")
        if root_pkg is not None:
            tree_blob_paths = [
                e["path"]
                for e in tree_entries
                if isinstance(e, dict)
                and e.get("type") == "blob"
                and isinstance(e.get("path"), str)
            ]
            workspace_paths = _expand_workspaces(
                root_pkg_content=root_pkg.content, tree_paths=tree_blob_paths
            )
            for ws_path in workspace_paths:
                try:
                    ws_file = await self._gh.get_file(
                        meta.owner, meta.name, ws_path, ref=meta.default_branch
                    )
                except GithubError as exc:
                    logger.warning("scanner: workspace fetch failed for %s: %s", ws_path, exc)
                    continue
                if ws_file is not None:
                    files[ws_path] = ws_file

        deps = _collect_dependencies(files)
        scan = _extract_stack(
            meta=meta,
            files=files,
            workflows=workflows,
            deps=deps,
            path_index=path_index,
        )
        # Optional LLM summary — soft-fails so a transient model error doesn't
        # tank the whole scan.
        await self._enrich_with_llm(scan)
        return scan

    async def _fetch_files(
        self,
        *,
        owner: str,
        name: str,
        ref: str,
        languages: dict[str, int],
    ) -> dict[str, GithubFile]:
        """Only fetch files we have a reason to think exist — avoids burning
        through GitHub's 60-req/hr unauthenticated budget on guaranteed 404s.
        Language hints are the cheapest signal.
        """
        candidate_paths: list[str] = []
        has_js = any(lang in languages for lang in ("JavaScript", "TypeScript"))
        has_py = "Python" in languages
        has_go = "Go" in languages
        has_rust = "Rust" in languages
        has_ruby = "Ruby" in languages
        has_php = "PHP" in languages
        has_java = any(lang in languages for lang in ("Java", "Kotlin", "Groovy"))

        # Manifests: only the ones consistent with the repo's languages.
        if has_js:
            candidate_paths += ["package.json", "tsconfig.json"]
        if has_py:
            candidate_paths += ["pyproject.toml", "requirements.txt", "Pipfile"]
        if has_go:
            candidate_paths.append("go.mod")
        if has_rust:
            candidate_paths.append("Cargo.toml")
        if has_ruby:
            candidate_paths.append("Gemfile")
        if has_php:
            candidate_paths.append("composer.json")
        if has_java:
            candidate_paths += ["pom.xml", "build.gradle", "build.gradle.kts"]

        # Generic config / infra files — try always, they're cheap to check.
        candidate_paths += [
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            "vercel.json",
            "netlify.toml",
            "fly.toml",
            "render.yaml",
            "serverless.yml",
            "Makefile",
            "README.md",
            "readme.md",
        ]
        if has_js:
            candidate_paths += ["next.config.js", "next.config.mjs", "vite.config.ts", "vite.config.js"]

        out: dict[str, GithubFile] = {}
        for path in candidate_paths:
            try:
                file = await self._gh.get_file(owner, name, path, ref=ref)
            except GithubError as exc:
                logger.warning("scanner: failed to fetch %s: %s", path, exc)
                continue
            if file is not None:
                out[path] = file
        return out

    async def _enrich_with_llm(self, scan: ScanResult) -> None:
        try:
            response = await self._ai.complete_json(
                system_prompt=_LLM_SYSTEM_PROMPT,
                user_prompt=_build_llm_prompt(scan=scan),
            )
            parsed = _ArchitectureSummary.model_validate(response.data)
        except (ValidationError, Exception) as exc:  # noqa: BLE001
            logger.warning("scanner: LLM enrichment failed, continuing without it: %s", exc)
            return
        scan.architecture_summary = parsed.architecture_summary
        # Defensive: even with the "1-3 words" prompt rule, some models return
        # a paragraph here. The DB column is VARCHAR(120) — truncate before
        # persist so we don't lose the rest of the enrichment.
        if parsed.business_domain:
            scan.business_domain = parsed.business_domain[:120]
        if parsed.strengths:
            scan.strengths = list(parsed.strengths)
        if parsed.highlights:
            scan.highlights = list(parsed.highlights)


# --- Helpers ---------------------------------------------------------------


def _collect_dependencies(files: dict[str, GithubFile]) -> set[str]:
    """Union of dep names found in any of the supported manifests.

    Returns lowercased names. JS deps keep their scope (`@aws-sdk/client-ssm`).
    Python deps are bare (`fastapi`). Go deps keep their module path.

    `package.json` is collected from the root AND any workspace manifests the
    scanner fetched (e.g. `apps/web/package.json`) — monorepos with empty
    root deps still surface their stack.
    """
    deps: set[str] = set()

    for path, file in files.items():
        if not path.endswith("package.json"):
            continue
        if not file.content:
            continue
        try:
            payload = json.loads(file.content)
        except (ValueError, AttributeError):
            continue
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            items = payload.get(section) or {}
            if isinstance(items, dict):
                for k in items.keys():
                    deps.add(k.lower())

    for path in ("requirements.txt", "Pipfile"):
        if (f := files.get(path)) and f.content:
            for line in f.content.splitlines():
                bare = line.split("#")[0].strip().split("==")[0].split(">=")[0].split("<=")[0]
                bare = bare.split("[")[0].strip().lower()
                if bare and not bare.startswith("-"):
                    deps.add(bare)

    if (poetry := files.get("pyproject.toml")) and poetry.content:
        import re as _re

        for raw in _re.findall(r'"([A-Za-z0-9_.\-]+)\s*(?:[<>=!~]|$)', poetry.content):
            name = raw.strip().lower()
            if name and name != "python" and len(name) > 1:
                deps.add(name)
        # Poetry-style: <name> = "<version>" lines under dependency sections
        in_deps = False
        for line in poetry.content.splitlines():
            stripped = line.strip()
            stripped_lc = stripped.lower()
            if stripped_lc.startswith("[tool.poetry") and "dependencies" in stripped_lc:
                in_deps = True
                continue
            if stripped_lc.startswith("[project.optional-dependencies"):
                in_deps = True
                continue
            if stripped.startswith("[") and not stripped_lc.startswith("[tool.poetry"):
                in_deps = False
            if in_deps and "=" in stripped and not stripped.startswith("#"):
                name = stripped.split("=", 1)[0].strip().strip('"').lower()
                if name and name != "python" and _re.match(r"^[a-z0-9_\-.]+$", name):
                    deps.add(name)

    if (gomod := files.get("go.mod")) and gomod.content:
        for line in gomod.content.splitlines():
            stripped = line.strip()
            if stripped.startswith("require "):
                rest = stripped.removeprefix("require ").strip().strip("(")
                if rest:
                    parts = rest.split()
                    if parts:
                        deps.add(parts[0].lower())
            elif "(" not in stripped and "/" in stripped and " " in stripped:
                # multi-line require block lines: "github.com/foo/bar v1.2.3"
                parts = stripped.split()
                if parts and "/" in parts[0]:
                    deps.add(parts[0].lower())

    if (cargo := files.get("Cargo.toml")) and cargo.content:
        for line in cargo.content.splitlines():
            stripped = line.strip()
            if "=" in stripped and not stripped.startswith("#") and not stripped.startswith("["):
                name = stripped.split("=", 1)[0].strip()
                if name and name.replace("-", "").replace("_", "").isalnum():
                    deps.add(name.lower())

    return deps


def _glob_to_regex(pattern: str) -> str:
    """Translate a `package.json` workspaces-style glob into a regex.

    Supports two wildcards (mirroring npm/yarn/pnpm semantics):
      `*`  — any single path segment (no `/`)
      `**` — any number of segments
    Everything else is escaped literally.
    """
    out: list[str] = []
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "*" and i + 1 < len(pattern) and pattern[i + 1] == "*":
            out.append(".+")
            i += 2
        elif ch == "*":
            out.append("[^/]+")
            i += 1
        else:
            out.append(re.escape(ch))
            i += 1
    return "".join(out)


# Workspaces in giant monorepos can be in the hundreds; cap fetches so a
# pathological repo doesn't blow our GitHub rate budget. 24 is generous —
# real monorepos usually declare 3–15.
MAX_WORKSPACES = 24


def _expand_workspaces(
    *,
    root_pkg_content: str | None,
    tree_paths: list[str],
) -> list[str]:
    """Resolve `workspaces` patterns in root `package.json` to concrete
    `package.json` paths inside the repo tree.

    Handles both the array form (`"workspaces": ["apps/*", "packages/*"]`)
    and the object form (`"workspaces": {"packages": [...]}`).
    """
    if not root_pkg_content:
        return []
    try:
        pkg = json.loads(root_pkg_content)
    except (ValueError, TypeError):
        return []

    raw = pkg.get("workspaces")
    if isinstance(raw, dict):
        patterns = raw.get("packages") or []
    elif isinstance(raw, list):
        patterns = raw
    else:
        return []
    if not isinstance(patterns, list):
        return []

    compiled: list[re.Pattern[str]] = []
    for pat in patterns:
        if not isinstance(pat, str) or not pat:
            continue
        regex = _glob_to_regex(pat.rstrip("/"))
        try:
            compiled.append(re.compile(rf"^{regex}$"))
        except re.error:
            continue
    if not compiled:
        return []

    out: list[str] = []
    seen: set[str] = set()
    for path in tree_paths:
        if not path.endswith("/package.json"):
            continue
        dir_path = path[: -len("/package.json")]
        if any(p.match(dir_path) for p in compiled) and path not in seen:
            seen.add(path)
            out.append(path)
            if len(out) >= MAX_WORKSPACES:
                break
    return out


def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _match_buckets(deps: set[str], catalog: dict[str, list[str]]) -> list[str]:
    """Conservative matcher: exact equality, or prefix match when the needle
    ends in `/` (npm scopes like `@aws-sdk/`, Go module paths). Substring
    matching produced false positives (the short needle "ai" lighting up on
    every `ai-…` package), so we require precise hits.
    """
    hits: list[str] = []
    for label, needles in catalog.items():
        for needle in needles:
            needle_lc = needle.lower()
            prefix = needle_lc.endswith("/")
            matched = (
                any(d.startswith(needle_lc) for d in deps)
                if prefix
                else needle_lc in deps
            )
            if matched:
                hits.append(label)
                break
    return hits


# Directories never worth indexing — vendor / build artifacts pollute the
# citation results without adding signal.
_PATH_INDEX_IGNORE_PREFIXES: tuple[str, ...] = (
    "node_modules/",
    ".git/",
    "dist/",
    "build/",
    "out/",
    ".next/",
    ".nuxt/",
    "target/",
    "vendor/",
    "venv/",
    ".venv/",
    "__pycache__/",
    ".tox/",
    "coverage/",
    ".pytest_cache/",
    ".idea/",
    ".vscode/",
    ".cache/",
)

# Extensions / filenames that signal "this is real code or meaningful config"
# — everything else (binaries, lockfiles, etc.) is skipped.
_PATH_INDEX_KEEP_EXTS: tuple[str, ...] = (
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".go", ".rs", ".java", ".kt", ".rb", ".php", ".cs", ".cpp", ".c", ".h",
    ".swift", ".scala", ".clj", ".ex", ".exs",
    ".sql", ".graphql", ".proto",
    ".yml", ".yaml", ".toml", ".tf", ".hcl",
    ".md",
)

_PATH_INDEX_KEEP_NAMES: tuple[str, ...] = (
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Makefile",
    "vercel.json",
    "netlify.toml",
    "fly.toml",
    "render.yaml",
    "serverless.yml",
    "wrangler.toml",
)

PATH_INDEX_LIMIT = 300


def _build_path_index(tree_entries: list[dict]) -> list[str]:
    """Filter a GitHub tree response down to a citation-friendly path list.

    Drops vendor folders + binary blobs, keeps source + meaningful config.
    Caps at PATH_INDEX_LIMIT so JSONB stays small.
    """
    out: list[str] = []
    for entry in tree_entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "blob":
            continue
        path = entry.get("path")
        if not isinstance(path, str) or not path:
            continue
        path_lc = path.lower()
        if any(path_lc.startswith(prefix) for prefix in _PATH_INDEX_IGNORE_PREFIXES):
            continue
        if any(f"/{prefix}" in path_lc for prefix in _PATH_INDEX_IGNORE_PREFIXES):
            continue
        basename = path.rsplit("/", 1)[-1]
        keep = (
            basename in _PATH_INDEX_KEEP_NAMES
            or any(path_lc.endswith(ext) for ext in _PATH_INDEX_KEEP_EXTS)
        )
        if not keep:
            continue
        out.append(path)
        if len(out) >= PATH_INDEX_LIMIT:
            break
    return out


def _extract_stack(
    *,
    meta,
    files: dict[str, GithubFile],
    workflows: list[str],
    deps: set[str],
    path_index: list[str],
) -> ScanResult:
    frameworks = _match_buckets(deps, FRAMEWORK_DEPS)
    databases = _match_buckets(deps, DATABASE_DEPS)
    authentication = _match_buckets(deps, AUTH_DEPS)
    ai_providers = _match_buckets(deps, AI_DEPS)
    cloud = _match_buckets(deps, CLOUD_DEPS)
    test_frameworks = _match_buckets(deps, TEST_DEPS)

    # File-based cloud signals (vercel.json, fly.toml, ...)
    for label, file_names in CLOUD_FILES.items():
        if any(fn in files for fn in file_names):
            if label not in cloud:
                cloud.append(label)

    has_docker = "Dockerfile" in files or "docker-compose.yml" in files or "docker-compose.yaml" in files
    ci_systems: list[str] = []
    if workflows:
        ci_systems.append("GitHub Actions")
    if ".gitlab-ci.yml" in files:
        ci_systems.append("GitLab CI")
    has_ci = bool(ci_systems)

    # Test frameworks: also infer from language presence (Go has built-in tests)
    if "Go" in meta.languages and "Go test" not in test_frameworks:
        test_frameworks.append("Go test")
    has_tests = bool(test_frameworks)

    readme_excerpt: str | None = None
    for readme_path in ("README.md", "readme.md"):
        if (r := files.get(readme_path)) and r.content:
            readme_excerpt = r.content[:4000]
            break

    # Libraries: a small high-signal subset of deps we didn't bucket elsewhere
    bucketed = {
        d.lower()
        for cat in (
            FRAMEWORK_DEPS,
            DATABASE_DEPS,
            AUTH_DEPS,
            AI_DEPS,
            CLOUD_DEPS,
            TEST_DEPS,
        )
        for needles in cat.values()
        for d in needles
    }
    notable_libs = [
        d for d in sorted(deps)
        if d not in bucketed
        and not d.startswith("@types/")
        and not d.startswith("eslint")
        and not d.startswith("prettier")
        and not d.startswith("typescript")
    ][:20]

    return ScanResult(
        owner=meta.owner,
        name=meta.name,
        default_branch=meta.default_branch,
        description=meta.description,
        languages=meta.languages,
        frameworks=_dedup(frameworks),
        libraries=_dedup(notable_libs),
        databases=_dedup(databases),
        authentication=_dedup(authentication),
        ai_providers=_dedup(ai_providers),
        cloud=_dedup(cloud),
        ci_systems=_dedup(ci_systems),
        test_frameworks=_dedup(test_frameworks),
        has_docker=has_docker,
        has_ci=has_ci,
        has_tests=has_tests,
        readme_excerpt=readme_excerpt,
        architecture_summary=None,
        business_domain=None,
        strengths=[],
        highlights=[],
        path_index=path_index,
    )
