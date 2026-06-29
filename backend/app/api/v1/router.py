from fastapi import APIRouter

from app.api.v1.endpoints import (
    analyses,
    analytics,
    applications,
    auth,
    confidence,
    evidence,
    health,
    jobs,
    matches,
    portfolio,
    portfolio_story,
    proposals,
    repositories,
    research,
    resume_recommendations,
    resumes,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(jobs.router)
api_router.include_router(analyses.router)
api_router.include_router(portfolio.router)
api_router.include_router(matches.router)
api_router.include_router(resumes.router)
api_router.include_router(resume_recommendations.router)
api_router.include_router(proposals.job_proposals_router)
api_router.include_router(proposals.proposals_router)
api_router.include_router(applications.router)
api_router.include_router(analytics.router)
api_router.include_router(repositories.router)
api_router.include_router(repositories.job_repository_matches_router)
api_router.include_router(evidence.router)
api_router.include_router(confidence.router)
api_router.include_router(research.router)
api_router.include_router(portfolio_story.router)
