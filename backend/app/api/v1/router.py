from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    admin_auth,
    analyses,
    analytics,
    applications,
    auth,
    career_fitness,
    career_pack,
    certificates,
    confidence,
    content_items,
    cv_uploads,
    evidence,
    health,
    jobs,
    linkedin,
    match_reports,
    matches,
    outputs,
    personas,
    portfolio,
    portfolio_story,
    proposals,
    repositories,
    research,
    resume_recommendations,
    resumes,
    students,
    tracker,
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
api_router.include_router(personas.router)
api_router.include_router(cv_uploads.router)
api_router.include_router(linkedin.router)
api_router.include_router(certificates.router)
api_router.include_router(content_items.router)
api_router.include_router(match_reports.router)
api_router.include_router(outputs.router)
api_router.include_router(career_fitness.router)
api_router.include_router(tracker.application_tracker_router)
api_router.include_router(tracker.tracker_router)
api_router.include_router(students.router)
# Career Starter Pack (post-CV LinkedIn/GitHub cards). Must come AFTER
# students.router so /students/career-pack doesn't get swallowed by
# students' wildcard prefix — but since neither uses a wildcard, order
# is defensive only.
api_router.include_router(career_pack.router)
# Order matters: /admin/auth before /admin so the auth prefix isn't
# swallowed by admin.router's CurrentAdmin gate.
api_router.include_router(admin_auth.router)
api_router.include_router(admin.router)
