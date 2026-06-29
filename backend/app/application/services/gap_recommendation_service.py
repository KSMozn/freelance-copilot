"""Turn missing skills into actionable recommendations.

Two-tier: deterministic rules for common skills (instant, free, predictable)
and an LLM-augmented path for the long tail. Phase E ships the deterministic
tier; the LLM tier is wired but disabled by default until Phase G hooks the
market signal into it.

Output is a list of :class:`GapRecommendation` objects, ordered by priority
(1 = highest). Each one tells the user *what concretely to do*:

    {
      "skill": "Kafka",
      "kind": "project_to_build",
      "suggestion": "Build a 200-event-per-second stream ...",
      "effort_estimate": "2-3 days",
      "priority": 1
    }
"""
from __future__ import annotations

from app.domain.entities.match_report import GapRecommendation, RecommendationKind


# Per-skill canned recommendations. Keyed by lowercase canonical name; falls
# back to a generic "learn it" prompt for anything we don't have rules for.
_RULES: dict[str, list[dict[str, object]]] = {
    "kafka": [
        {
            "kind": "project_to_build",
            "suggestion": "Build a small event-driven pipeline that consumes a public webhook, "
            "publishes to a local Kafka topic, and stores aggregates in Postgres. Wire up a "
            "Docker Compose with kafka + a worker.",
            "effort_estimate": "2-3 days",
        },
        {
            "kind": "github_enhancement",
            "suggestion": "Add an `events/` module to your strongest backend repo that uses "
            "Kafka topics for inter-service messaging, with a README diagram.",
            "effort_estimate": "1 day",
        },
    ],
    "rabbitmq": [
        {
            "kind": "project_to_build",
            "suggestion": "Stand up a RabbitMQ broker with two consumers + a dead-letter queue. "
            "Document throughput numbers in a short blog post.",
            "effort_estimate": "1-2 days",
        }
    ],
    "kubernetes": [
        {
            "kind": "certification",
            "suggestion": "CKAD (Certified Kubernetes Application Developer) is the most cited "
            "in job postings; cheaper + faster than CKA.",
            "effort_estimate": "2-3 weeks",
        },
        {
            "kind": "project_to_build",
            "suggestion": "Convert one of your scanned repos to a Helm chart with HPA and a "
            "PodDisruptionBudget; deploy to a free-tier cluster.",
            "effort_estimate": "1 week",
        },
    ],
    "terraform": [
        {
            "kind": "project_to_build",
            "suggestion": "Author a Terraform module that provisions a VPC + RDS + ALB, complete "
            "with terratest coverage. Publish to the registry under your handle.",
            "effort_estimate": "3-5 days",
        }
    ],
    "graphql": [
        {
            "kind": "github_enhancement",
            "suggestion": "Add a GraphQL gateway (Strawberry / Apollo) in front of an existing "
            "REST repo and document the migration.",
            "effort_estimate": "2-3 days",
        }
    ],
    "rag": [
        {
            "kind": "project_to_build",
            "suggestion": "Ship a RAG demo: ingest 50 PDFs via pdfminer, embed with OpenAI, "
            "store in pgvector, answer with a small FastAPI endpoint + citations.",
            "effort_estimate": "3-5 days",
        }
    ],
    "retrieval-augmented generation": [
        {
            "kind": "project_to_build",
            "suggestion": "Ship a RAG demo: ingest 50 PDFs via pdfminer, embed with OpenAI, "
            "store in pgvector, answer with a small FastAPI endpoint + citations.",
            "effort_estimate": "3-5 days",
        }
    ],
    "aws": [
        {
            "kind": "certification",
            "suggestion": "AWS Solutions Architect — Associate is the most-recognized starting "
            "cert. Skip the Cloud Practitioner unless you need a primer.",
            "effort_estimate": "4-6 weeks",
        }
    ],
    "gcp": [
        {
            "kind": "certification",
            "suggestion": "GCP Professional Cloud Developer is the closest to engineering-focused "
            "job descriptions.",
            "effort_estimate": "4-6 weeks",
        }
    ],
    "azure": [
        {
            "kind": "certification",
            "suggestion": "Azure AZ-204 (Developing Solutions for Azure) is the most-cited dev "
            "cert. Pair with AZ-104 for SA-leaning roles.",
            "effort_estimate": "4-6 weeks",
        }
    ],
    "leadership": [
        {
            "kind": "experience_to_emphasize",
            "suggestion": "Pin your most-recent lead role under your Tech Lead / Manager persona "
            "and add 2-3 concrete leadership achievements (team size, decisions you owned).",
            "effort_estimate": "30 minutes",
        }
    ],
    "mentoring": [
        {
            "kind": "experience_to_emphasize",
            "suggestion": "Add a 'Mentorship' subsection to your CV with the number of "
            "engineers you've onboarded or unblocked.",
            "effort_estimate": "30 minutes",
        }
    ],
}


_FALLBACK = {
    "kind": "learning_resource",
    "suggestion_template": (
        "Pick the top-rated official tutorial for {skill} and ship a 200-line proof-of-concept "
        "to a public repo. Mention it in your CV summary."
    ),
    "effort_estimate": "1-2 days",
}


class GapRecommendationService:
    """Produces a ranked list of actionable suggestions from a missing-skill list.

    The constructor is intentionally lightweight — no provider, no DB — so
    callers (e.g. ``MatchReportService``) can instantiate per-request and
    feed it the persona / job context.
    """

    def recommend(
        self,
        *,
        missing_skills: list[dict[str, object]],
        max_recommendations: int = 6,
    ) -> list[GapRecommendation]:
        """Return up to ``max_recommendations`` ordered by priority.

        ``missing_skills`` is the shape produced by ``SkillEvidenceService``:
            [{name: str, importance: int 1..5, status: "missing"|"weak"}, ...]
        """
        recs: list[GapRecommendation] = []
        for entry in missing_skills:
            name = str(entry.get("name", "")).strip()
            if not name:
                continue
            importance = int(entry.get("importance") or 3)
            for template in _rules_for(name) or [_fallback_template(name)]:
                recs.append(
                    GapRecommendation(
                        skill=name,
                        kind=template["kind"],  # type: ignore[arg-type]
                        suggestion=str(template["suggestion"]),
                        effort_estimate=str(template["effort_estimate"]),
                        # Priority: importance is 1..5 (higher = critical).
                        # Map to recommendation priority where 1 is highest.
                        priority=max(1, 6 - importance),
                    )
                )
        recs.sort(key=lambda r: (r.priority, r.skill.lower()))
        return recs[:max_recommendations]


def _rules_for(name: str) -> list[dict[str, object]]:
    return _RULES.get(name.strip().lower(), [])


def _fallback_template(skill: str) -> dict[str, object]:
    suggestion = _FALLBACK["suggestion_template"].format(skill=skill)  # type: ignore[union-attr]
    return {
        "kind": _FALLBACK["kind"],
        "suggestion": suggestion,
        "effort_estimate": _FALLBACK["effort_estimate"],
    }
