"""phase B: seed common skills into the catalog

A bootstrap list of well-known languages, frameworks, tools, platforms,
databases, practices, and soft skills. Idempotent — re-running the seed
won't duplicate rows.

The list is intentionally tight (~120 entries). Free-form user-added skills
and skills auto-derived from scanned repos / parsed CVs / portfolios will
expand the catalog organically; this is just the cold-start surface.

Revision ID: 0018_phase_b_seed_catalog
Revises: 0017_phase_b_graph_core
Create Date: 2026-06-29
"""
from __future__ import annotations

import json

import sqlalchemy as sa

from alembic import op

revision = "0018_phase_b_seed_catalog"
down_revision = "0017_phase_b_graph_core"
branch_labels = None
depends_on = None


# (slug, name, category, aliases)
SEED_SKILLS: list[tuple[str, str, str, list[str]]] = [
    # ---- Languages ----
    ("python", "Python", "language", ["py", "python3"]),
    ("typescript", "TypeScript", "language", ["ts"]),
    ("javascript", "JavaScript", "language", ["js", "node", "nodejs"]),
    ("go", "Go", "language", ["golang"]),
    ("rust", "Rust", "language", []),
    ("java", "Java", "language", []),
    ("kotlin", "Kotlin", "language", []),
    ("swift", "Swift", "language", []),
    ("ruby", "Ruby", "language", []),
    ("php", "PHP", "language", []),
    ("c-sharp", "C#", "language", ["csharp", "dotnet", ".net"]),
    ("c-plus-plus", "C++", "language", ["cpp", "cplusplus"]),
    ("sql", "SQL", "language", []),
    ("html", "HTML", "language", ["html5"]),
    ("css", "CSS", "language", ["css3"]),
    ("bash", "Bash", "language", ["shell", "sh"]),
    ("r", "R", "language", []),
    ("scala", "Scala", "language", []),
    # ---- Frameworks (web) ----
    ("fastapi", "FastAPI", "framework", []),
    ("django", "Django", "framework", []),
    ("flask", "Flask", "framework", []),
    ("express", "Express", "framework", ["expressjs"]),
    ("nestjs", "NestJS", "framework", ["nest"]),
    ("nextjs", "Next.js", "framework", ["next"]),
    ("react", "React", "framework", ["reactjs"]),
    ("vue", "Vue", "framework", ["vuejs", "vue.js"]),
    ("angular", "Angular", "framework", []),
    ("svelte", "Svelte", "framework", ["sveltekit"]),
    ("spring", "Spring", "framework", ["spring-boot", "springboot"]),
    ("rails", "Rails", "framework", ["ruby-on-rails", "ror"]),
    ("laravel", "Laravel", "framework", []),
    ("dot-net", ".NET", "framework", ["aspnet", "asp.net"]),
    ("remix", "Remix", "framework", []),
    # ---- Frameworks (mobile / desktop) ----
    ("react-native", "React Native", "framework", ["rn"]),
    ("flutter", "Flutter", "framework", []),
    ("electron", "Electron", "framework", []),
    # ---- Frameworks (AI / ML) ----
    ("pytorch", "PyTorch", "framework", ["torch"]),
    ("tensorflow", "TensorFlow", "framework", ["tf"]),
    ("hugging-face", "Hugging Face", "framework", ["huggingface", "transformers"]),
    ("langchain", "LangChain", "framework", []),
    ("llamaindex", "LlamaIndex", "framework", []),
    # ---- Databases ----
    ("postgresql", "PostgreSQL", "database", ["postgres", "psql", "pg"]),
    ("mysql", "MySQL", "database", []),
    ("sqlite", "SQLite", "database", []),
    ("mongodb", "MongoDB", "database", ["mongo"]),
    ("redis", "Redis", "database", []),
    ("elasticsearch", "Elasticsearch", "database", ["elastic", "opensearch"]),
    ("clickhouse", "ClickHouse", "database", []),
    ("cassandra", "Cassandra", "database", []),
    ("dynamodb", "DynamoDB", "database", []),
    ("neo4j", "Neo4j", "database", []),
    ("pgvector", "pgvector", "database", []),
    ("pinecone", "Pinecone", "database", []),
    ("weaviate", "Weaviate", "database", []),
    # ---- Platforms / Cloud ----
    ("aws", "AWS", "platform", ["amazon-web-services"]),
    ("gcp", "Google Cloud", "platform", ["google-cloud", "google-cloud-platform"]),
    ("azure", "Azure", "platform", ["microsoft-azure"]),
    ("kubernetes", "Kubernetes", "platform", ["k8s"]),
    ("docker", "Docker", "platform", []),
    ("vercel", "Vercel", "platform", []),
    ("netlify", "Netlify", "platform", []),
    ("heroku", "Heroku", "platform", []),
    ("cloudflare", "Cloudflare", "platform", ["cf-workers", "cloudflare-workers"]),
    ("fly-io", "Fly.io", "platform", ["fly"]),
    ("railway", "Railway", "platform", []),
    ("supabase", "Supabase", "platform", []),
    ("firebase", "Firebase", "platform", []),
    # ---- Tools ----
    ("git", "Git", "tool", []),
    ("github-actions", "GitHub Actions", "tool", ["gh-actions"]),
    ("gitlab-ci", "GitLab CI", "tool", []),
    ("terraform", "Terraform", "tool", []),
    ("pulumi", "Pulumi", "tool", []),
    ("ansible", "Ansible", "tool", []),
    ("nginx", "Nginx", "tool", []),
    ("graphql", "GraphQL", "tool", []),
    ("rest", "REST", "tool", ["rest-api"]),
    ("grpc", "gRPC", "tool", []),
    ("kafka", "Kafka", "tool", ["apache-kafka"]),
    ("rabbitmq", "RabbitMQ", "tool", []),
    ("celery", "Celery", "tool", []),
    ("webpack", "Webpack", "tool", []),
    ("vite", "Vite", "tool", []),
    ("playwright", "Playwright", "tool", []),
    ("cypress", "Cypress", "tool", []),
    ("pytest", "pytest", "tool", []),
    ("jest", "Jest", "tool", []),
    # ---- AI / LLM providers ----
    ("openai", "OpenAI", "platform", ["gpt", "chatgpt"]),
    ("anthropic", "Anthropic", "platform", ["claude"]),
    ("groq", "Groq", "platform", []),
    ("cohere", "Cohere", "platform", []),
    # ---- Practices ----
    ("system-design", "System Design", "practice", []),
    ("microservices", "Microservices", "practice", []),
    ("event-driven", "Event-Driven Architecture", "practice", ["event-driven-arch", "eda"]),
    ("cqrs", "CQRS", "practice", []),
    ("ddd", "Domain-Driven Design", "practice", ["domain-driven-design"]),
    ("tdd", "Test-Driven Development", "practice", ["test-driven-development"]),
    ("code-review", "Code Review", "practice", []),
    ("rag", "Retrieval-Augmented Generation", "practice", ["retrieval-augmented-generation"]),
    ("fine-tuning", "Fine-Tuning", "practice", ["finetuning"]),
    ("prompt-engineering", "Prompt Engineering", "practice", []),
    ("ci-cd", "CI/CD", "practice", ["cicd", "continuous-integration", "continuous-delivery"]),
    ("agile", "Agile", "practice", ["scrum", "kanban"]),
    ("observability", "Observability", "practice", ["monitoring"]),
    ("security", "Security", "practice", ["appsec", "infosec"]),
    # ---- Leadership / Soft ----
    ("communication", "Communication", "soft", []),
    ("stakeholder-mgmt", "Stakeholder Management", "soft", ["stakeholder-management"]),
    ("conflict-resolution", "Conflict Resolution", "soft", []),
    ("technical-writing", "Technical Writing", "soft", []),
    ("public-speaking", "Public Speaking", "soft", []),
    ("mentoring", "Mentoring", "leadership", ["mentorship"]),
    ("team-leadership", "Team Leadership", "leadership", []),
    ("hiring", "Hiring", "leadership", ["recruiting"]),
    ("project-management", "Project Management", "leadership", []),
    ("performance-mgmt", "Performance Management", "leadership", ["performance-management"]),
    ("strategy", "Technical Strategy", "leadership", []),
    # ---- Domains ----
    ("fintech", "FinTech", "domain", ["finance", "financial-services"]),
    ("healthtech", "HealthTech", "domain", ["healthcare", "health-tech"]),
    ("edtech", "EdTech", "domain", ["education"]),
    ("ecommerce", "E-commerce", "domain", ["e-commerce", "retail"]),
    ("saas", "SaaS", "domain", ["b2b-saas"]),
    ("ai-ml", "AI / ML", "domain", ["ai", "ml", "machine-learning", "artificial-intelligence"]),
    ("data-platform", "Data Platform", "domain", ["data-engineering", "data-platforms"]),
    ("devtools", "Developer Tools", "domain", ["dev-tools"]),
    ("media", "Media / Streaming", "domain", ["streaming"]),
    ("iot", "IoT / Industrial", "domain", ["iot", "industrial"]),
]


def upgrade() -> None:
    conn = op.get_bind()
    sql = sa.text(
        """
        INSERT INTO skill_catalog (slug, name, category, aliases, is_system_seeded)
        VALUES (:slug, :name, :category, CAST(:aliases AS jsonb), true)
        ON CONFLICT (slug) DO NOTHING
        """
    )
    inserted = 0
    for slug, name, category, aliases in SEED_SKILLS:
        result = conn.execute(
            sql,
            {
                "slug": slug,
                "name": name,
                "category": category,
                "aliases": json.dumps(aliases),
            },
        )
        if result.rowcount:
            inserted += 1
    print(f"[phase B seed] inserted {inserted} of {len(SEED_SKILLS)} catalog rows")


def downgrade() -> None:
    conn = op.get_bind()
    slugs = [s[0] for s in SEED_SKILLS]
    conn.execute(
        sa.text(
            "DELETE FROM skill_catalog WHERE is_system_seeded = true AND slug = ANY(:slugs)"
        ),
        {"slugs": slugs},
    )
