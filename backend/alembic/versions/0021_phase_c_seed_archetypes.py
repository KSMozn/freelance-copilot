"""phase C: seed 11 persona archetypes

Each archetype ships:
  * sensible scoring `default_weights` (sum = 100, keys match
    FreelancerProfile.weights)
  * `default_skill_category_weights` (sums to 1.0) — used by future
    services to bias skill evidence ranking
  * `default_proposal_tone` and `default_target_roles`
  * `default_seniority_band` — feeds resume↔job seniority alignment

Idempotent: re-runs upsert by slug.

Revision ID: 0021_phase_c_seed_archetypes
Revises: 0020_phase_c_personas
Create Date: 2026-06-29
"""
from __future__ import annotations

import json

import sqlalchemy as sa
from alembic import op


revision = "0021_phase_c_seed_archetypes"
down_revision = "0020_phase_c_personas"
branch_labels = None
depends_on = None


# (slug, name, description, default_weights, default_skill_category_weights,
#  default_proposal_tone, default_target_roles, default_seniority_band)
ARCHETYPES: list[tuple[str, str, str, dict, dict, str, list[str], str | None]] = [
    (
        "individual_contributor",
        "Individual Contributor",
        "Hands-on builder. Hired to ship features end-to-end with minimal coordination overhead.",
        {
            "technical_fit": 40,
            "domain_fit": 5,
            "proposal_count": 15,
            "budget_attractiveness": 15,
            "client_quality": 5,
            "estimated_effort": 10,
            "risk_level": 5,
            "strategic_value": 5,
        },
        {"language": 0.30, "framework": 0.25, "tool": 0.15, "database": 0.15, "platform": 0.10, "soft": 0.05},
        "technical_deep",
        ["Software Engineer", "Backend Engineer", "Frontend Engineer", "Full-Stack Engineer"],
        "mid",
    ),
    (
        "senior_engineer",
        "Senior Engineer",
        "Experienced builder trusted to own significant scope and mentor mids.",
        {
            "technical_fit": 35,
            "domain_fit": 10,
            "proposal_count": 15,
            "budget_attractiveness": 12,
            "client_quality": 8,
            "estimated_effort": 10,
            "risk_level": 5,
            "strategic_value": 5,
        },
        {"language": 0.25, "framework": 0.25, "practice": 0.20, "database": 0.10, "platform": 0.10, "soft": 0.10},
        "pragmatic",
        ["Senior Software Engineer", "Senior Backend Engineer", "Senior Full-Stack Engineer"],
        "senior",
    ),
    (
        "tech_lead",
        "Tech Lead",
        "Owns the technical direction of a single team. Hands-on but also coordinating, reviewing, mentoring.",
        {
            "technical_fit": 30,
            "domain_fit": 10,
            "proposal_count": 15,
            "budget_attractiveness": 10,
            "client_quality": 10,
            "estimated_effort": 10,
            "risk_level": 10,
            "strategic_value": 5,
        },
        {"practice": 0.25, "framework": 0.20, "leadership": 0.20, "language": 0.15, "platform": 0.10, "soft": 0.10},
        "pragmatic",
        ["Tech Lead", "Engineering Lead", "Lead Engineer"],
        "senior",
    ),
    (
        "staff_engineer",
        "Staff Engineer",
        "Senior IC scope: cross-team technical strategy, architecture, system design across services.",
        {
            "technical_fit": 25,
            "domain_fit": 15,
            "proposal_count": 10,
            "budget_attractiveness": 15,
            "client_quality": 15,
            "estimated_effort": 5,
            "risk_level": 10,
            "strategic_value": 5,
        },
        {"practice": 0.30, "platform": 0.20, "leadership": 0.15, "framework": 0.15, "domain": 0.10, "soft": 0.10},
        "consultative",
        ["Staff Engineer", "Staff Software Engineer"],
        "staff",
    ),
    (
        "principal_engineer",
        "Principal Engineer",
        "Organization-wide technical leadership. Strategy, architecture review, hard tradeoffs.",
        {
            "technical_fit": 20,
            "domain_fit": 20,
            "proposal_count": 10,
            "budget_attractiveness": 15,
            "client_quality": 15,
            "estimated_effort": 5,
            "risk_level": 10,
            "strategic_value": 5,
        },
        {"practice": 0.30, "platform": 0.20, "leadership": 0.20, "domain": 0.15, "framework": 0.10, "soft": 0.05},
        "consultative",
        ["Principal Engineer", "Principal Software Engineer", "Distinguished Engineer"],
        "principal",
    ),
    (
        "engineering_manager",
        "Engineering Manager",
        "People-first leader of a team. Hiring, performance, planning, stakeholder management.",
        {
            "technical_fit": 15,
            "domain_fit": 15,
            "proposal_count": 10,
            "budget_attractiveness": 15,
            "client_quality": 20,
            "estimated_effort": 10,
            "risk_level": 10,
            "strategic_value": 5,
        },
        {"leadership": 0.30, "soft": 0.25, "practice": 0.20, "domain": 0.15, "framework": 0.05, "platform": 0.05},
        "executive",
        ["Engineering Manager", "Software Engineering Manager", "EM"],
        "manager",
    ),
    (
        "director_of_engineering",
        "Director of Engineering",
        "Multi-team leadership. Org design, strategy, exec stakeholder, hiring leadership.",
        {
            "technical_fit": 10,
            "domain_fit": 20,
            "proposal_count": 5,
            "budget_attractiveness": 20,
            "client_quality": 25,
            "estimated_effort": 5,
            "risk_level": 10,
            "strategic_value": 5,
        },
        {"leadership": 0.35, "soft": 0.30, "domain": 0.20, "practice": 0.10, "platform": 0.05},
        "executive",
        ["Director of Engineering", "Head of Engineering", "VP of Engineering"],
        "director",
    ),
    (
        "ai_engineer",
        "AI Engineer",
        "Builds AI-powered features end-to-end: prompts, embeddings, RAG, agents, evaluation, deployment.",
        {
            "technical_fit": 35,
            "domain_fit": 15,
            "proposal_count": 10,
            "budget_attractiveness": 15,
            "client_quality": 10,
            "estimated_effort": 5,
            "risk_level": 5,
            "strategic_value": 5,
        },
        {"framework": 0.25, "language": 0.20, "platform": 0.20, "practice": 0.20, "tool": 0.10, "domain": 0.05},
        "technical_deep",
        ["AI Engineer", "ML Engineer", "Applied AI Engineer", "LLM Engineer"],
        "senior",
    ),
    (
        "solutions_architect",
        "Solutions Architect",
        "Customer-facing technical lead. Bridges business problems to architecture; advises engineering teams.",
        {
            "technical_fit": 25,
            "domain_fit": 20,
            "proposal_count": 10,
            "budget_attractiveness": 15,
            "client_quality": 15,
            "estimated_effort": 5,
            "risk_level": 5,
            "strategic_value": 5,
        },
        {"platform": 0.25, "practice": 0.25, "domain": 0.20, "framework": 0.15, "database": 0.10, "soft": 0.05},
        "consultative",
        ["Solutions Architect", "Principal Consultant", "Solutions Engineer"],
        "senior",
    ),
    (
        "consultant",
        "Consultant",
        "Engaged for specific outcomes — assessments, audits, hands-on delivery of bounded scope.",
        {
            "technical_fit": 20,
            "domain_fit": 25,
            "proposal_count": 10,
            "budget_attractiveness": 15,
            "client_quality": 15,
            "estimated_effort": 5,
            "risk_level": 5,
            "strategic_value": 5,
        },
        {"domain": 0.30, "practice": 0.25, "soft": 0.20, "framework": 0.10, "platform": 0.10, "tool": 0.05},
        "consultative",
        ["Independent Consultant", "Technical Consultant", "Software Consultant"],
        "senior",
    ),
    (
        "freelancer",
        "Freelancer",
        "Independent operator. Project-based engagements, often across multiple clients, end-to-end.",
        {
            "technical_fit": 30,
            "domain_fit": 10,
            "proposal_count": 20,
            "budget_attractiveness": 15,
            "client_quality": 5,
            "estimated_effort": 10,
            "risk_level": 5,
            "strategic_value": 5,
        },
        {"language": 0.25, "framework": 0.25, "tool": 0.15, "soft": 0.15, "platform": 0.10, "database": 0.10},
        "pragmatic",
        ["Freelance Engineer", "Independent Contractor", "Freelance Developer"],
        "senior",
    ),
]


def upgrade() -> None:
    conn = op.get_bind()
    sql = sa.text(
        """
        INSERT INTO persona_archetypes (
            slug, name, description,
            default_weights, default_skill_category_weights,
            default_proposal_tone, default_target_roles, default_seniority_band,
            sort_order
        )
        VALUES (
            :slug, :name, :description,
            CAST(:weights AS jsonb), CAST(:category_weights AS jsonb),
            :tone, CAST(:roles AS jsonb), :seniority,
            :sort_order
        )
        ON CONFLICT (slug) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            default_weights = EXCLUDED.default_weights,
            default_skill_category_weights = EXCLUDED.default_skill_category_weights,
            default_proposal_tone = EXCLUDED.default_proposal_tone,
            default_target_roles = EXCLUDED.default_target_roles,
            default_seniority_band = EXCLUDED.default_seniority_band,
            sort_order = EXCLUDED.sort_order
        """
    )
    for idx, row in enumerate(ARCHETYPES):
        slug, name, desc, weights, cat_weights, tone, roles, seniority = row
        conn.execute(
            sql,
            {
                "slug": slug,
                "name": name,
                "description": desc,
                "weights": json.dumps(weights),
                "category_weights": json.dumps(cat_weights),
                "tone": tone,
                "roles": json.dumps(roles),
                "seniority": seniority,
                "sort_order": idx,
            },
        )
    print(f"[phase C seed] upserted {len(ARCHETYPES)} persona archetypes")


def downgrade() -> None:
    conn = op.get_bind()
    slugs = [r[0] for r in ARCHETYPES]
    conn.execute(
        sa.text("DELETE FROM persona_archetypes WHERE slug = ANY(:slugs)"),
        {"slugs": slugs},
    )
