"""phase B: backfill user_skills + projects from existing data

Aggregates skill strings already living in `resumes.primary_skills`,
`resumes.secondary_skills`, `resumes.keywords`, `portfolios.technologies`,
`portfolios.skills`, and `repositories.{languages, frameworks, libraries,
databases, authentication, ai_providers, cloud, ci_systems, test_frameworks}`
into `user_skills`. Unknown strings are added to `skill_catalog` with
`is_system_seeded=false` and `category='tool'` as a sensible neutral default.

Also creates one `projects` row per existing portfolio (origin=portfolio)
and one per existing scanned repository (origin=repo), linked back via
`projects.portfolio_id` / `projects.repo_id`.

Idempotent: `ON CONFLICT DO NOTHING` on unique constraints; safe to re-run.

Revision ID: 0019_phase_b_backfill
Revises: 0018_phase_b_seed_catalog
Create Date: 2026-06-29
"""
from __future__ import annotations

import json
import re

import sqlalchemy as sa
from alembic import op


revision = "0019_phase_b_backfill"
down_revision = "0018_phase_b_seed_catalog"
branch_labels = None
depends_on = None


_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _slugify(name: str) -> str:
    s = name.strip().lower()
    s = _SLUG_NON_ALNUM.sub("-", s).strip("-")
    return s or "unknown"


def _resolve_skill_id(conn: sa.engine.Connection, raw_name: str) -> str | None:
    """Find or create a `skill_catalog` row for ``raw_name``, return its id.

    Lookup order: exact slug match → alias match → fuzzy trigram (>=0.85) →
    create new row marked `is_system_seeded=false`.
    """
    name = raw_name.strip()
    if not name or len(name) > 120:
        return None
    slug = _slugify(name)

    # Exact slug
    row = conn.execute(
        sa.text("SELECT id FROM skill_catalog WHERE slug = :slug"), {"slug": slug}
    ).fetchone()
    if row:
        return str(row[0])

    # Alias match (JSONB contains)
    row = conn.execute(
        sa.text(
            "SELECT id FROM skill_catalog WHERE aliases @> CAST(:needle AS jsonb) LIMIT 1"
        ),
        {"needle": json.dumps([slug])},
    ).fetchone()
    if row:
        return str(row[0])

    # Fuzzy trigram against name (requires pg_trgm — installed in 0016)
    row = conn.execute(
        sa.text(
            """
            SELECT id FROM skill_catalog
            WHERE similarity(name, :name) >= 0.85
            ORDER BY similarity(name, :name) DESC
            LIMIT 1
            """
        ),
        {"name": name},
    ).fetchone()
    if row:
        return str(row[0])

    # Create new (free-form). Default category 'tool' — operator can recategorize.
    row = conn.execute(
        sa.text(
            """
            INSERT INTO skill_catalog (slug, name, category, aliases, is_system_seeded)
            VALUES (:slug, :name, 'tool', CAST('[]' AS jsonb), false)
            ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """
        ),
        {"slug": slug, "name": name},
    ).fetchone()
    return str(row[0]) if row else None


def upgrade() -> None:
    conn = op.get_bind()

    # ---- 1. Aggregate skills per user from resumes / portfolios / repositories ----
    # Pull raw strings + which source supplied them, so user_skills.sources is
    # a useful provenance map.

    skill_aggregates: dict[tuple[str, str], dict] = {}
    # key: (user_id, skill_catalog_id)
    # value: {"sources": {"resume_ids": [...], "portfolio_ids": [...], ...},
    #         "evidence_count": int}

    def _add(user_id: str, raw_name: str, source_field: str, source_ref: str) -> None:
        skill_id = _resolve_skill_id(conn, raw_name)
        if skill_id is None:
            return
        key = (user_id, skill_id)
        entry = skill_aggregates.setdefault(
            key,
            {
                "sources": {
                    "resume_ids": [],
                    "portfolio_ids": [],
                    "repo_ids": [],
                    "manual": False,
                    "ai_suggested": False,
                },
                "evidence_count": 0,
            },
        )
        entry["sources"][source_field].append(source_ref)
        entry["evidence_count"] += 1

    # Resumes
    resumes = conn.execute(
        sa.text(
            "SELECT id, user_id, primary_skills, secondary_skills, keywords FROM resumes"
        )
    ).fetchall()
    for resume_id, user_id, primary, secondary, keywords in resumes:
        for raw in (primary or []) + (secondary or []) + (keywords or []):
            if isinstance(raw, str) and raw.strip():
                _add(str(user_id), raw, "resume_ids", str(resume_id))

    # Portfolios
    portfolios = conn.execute(
        sa.text("SELECT id, user_id, technologies, skills FROM portfolios")
    ).fetchall()
    for portfolio_id, user_id, technologies, skills in portfolios:
        for raw in (technologies or []) + (skills or []):
            if isinstance(raw, str) and raw.strip():
                _add(str(user_id), raw, "portfolio_ids", str(portfolio_id))

    # Repositories — derived from languages (dict) + multiple list columns.
    repos = conn.execute(
        sa.text(
            """
            SELECT id, user_id, languages, frameworks, libraries, databases,
                   authentication, ai_providers, cloud, ci_systems, test_frameworks
            FROM repositories
            """
        )
    ).fetchall()
    for row in repos:
        repo_id = str(row[0])
        user_id = str(row[1])
        languages = row[2] or {}
        flat: list[str] = []
        if isinstance(languages, dict):
            flat.extend(languages.keys())
        for col in row[3:]:
            if isinstance(col, list):
                flat.extend(x for x in col if isinstance(x, str) and x.strip())
        for raw in flat:
            _add(user_id, raw, "repo_ids", repo_id)

    # ---- 2. Insert user_skills rows ----
    insert_us = sa.text(
        """
        INSERT INTO user_skills (user_id, skill_id, proficiency, sources, evidence_count)
        VALUES (
            CAST(:user_id AS uuid),
            CAST(:skill_id AS uuid),
            :proficiency,
            CAST(:sources AS jsonb),
            :evidence_count
        )
        ON CONFLICT (user_id, skill_id) DO UPDATE SET
            sources = EXCLUDED.sources,
            evidence_count = EXCLUDED.evidence_count
        """
    )
    inserted = 0
    for (user_id, skill_id), payload in skill_aggregates.items():
        # Proficiency heuristic for backfill: 3 (mid) by default; bump to 4 if
        # seen ≥3 sources, 5 if ≥6. Real proficiencies will come from user input.
        ec = payload["evidence_count"]
        proficiency = 5 if ec >= 6 else (4 if ec >= 3 else 3)
        conn.execute(
            insert_us,
            {
                "user_id": user_id,
                "skill_id": skill_id,
                "proficiency": proficiency,
                "sources": json.dumps(payload["sources"]),
                "evidence_count": ec,
            },
        )
        inserted += 1
    print(f"[phase B backfill] inserted {inserted} user_skills rows")

    # ---- 3. Create projects from portfolios + repositories ----
    insert_proj = sa.text(
        """
        INSERT INTO projects (user_id, name, summary, role, portfolio_id, repo_id, origin)
        VALUES (
            CAST(:user_id AS uuid),
            :name,
            :summary,
            :role,
            CAST(:portfolio_id AS uuid),
            CAST(:repo_id AS uuid),
            :origin
        )
        """
    )

    portfolio_rows = conn.execute(
        sa.text(
            "SELECT id, user_id, title, COALESCE(short_description, long_description), role "
            "FROM portfolios"
        )
    ).fetchall()
    proj_count = 0
    for pf_id, user_id, title, summary, role in portfolio_rows:
        # Don't double-insert if a project already exists for this portfolio
        # (idempotency for re-runs).
        exists = conn.execute(
            sa.text(
                "SELECT 1 FROM projects WHERE portfolio_id = CAST(:pid AS uuid) LIMIT 1"
            ),
            {"pid": str(pf_id)},
        ).fetchone()
        if exists:
            continue
        conn.execute(
            insert_proj,
            {
                "user_id": str(user_id),
                "name": title or "Untitled project",
                "summary": (summary or "")[:2000] or None,
                "role": role,
                "portfolio_id": str(pf_id),
                "repo_id": None,
                "origin": "portfolio",
            },
        )
        proj_count += 1

    repo_rows = conn.execute(
        sa.text(
            "SELECT id, user_id, COALESCE(name, github_url), "
            "       COALESCE(description, architecture_summary) "
            "FROM repositories"
        )
    ).fetchall()
    for r_id, user_id, name, summary in repo_rows:
        exists = conn.execute(
            sa.text(
                "SELECT 1 FROM projects WHERE repo_id = CAST(:rid AS uuid) LIMIT 1"
            ),
            {"rid": str(r_id)},
        ).fetchone()
        if exists:
            continue
        conn.execute(
            insert_proj,
            {
                "user_id": str(user_id),
                "name": name or "Untitled repository",
                "summary": (summary or "")[:2000] or None,
                "role": None,
                "portfolio_id": None,
                "repo_id": str(r_id),
                "origin": "repo",
            },
        )
        proj_count += 1
    print(f"[phase B backfill] inserted {proj_count} projects rows")


def downgrade() -> None:
    # Pure data migration — clear the rows it created. Catalog rows added with
    # is_system_seeded=false stay (they may have been edited by users).
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM projects WHERE origin IN ('repo', 'portfolio')"))
    conn.execute(
        sa.text(
            "DELETE FROM user_skills "
            "WHERE sources ?| ARRAY['resume_ids', 'portfolio_ids', 'repo_ids']"
        )
    )
