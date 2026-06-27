from fastapi import APIRouter

from app.api.v1.endpoints import analyses, auth, health, jobs, matches, portfolio

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(jobs.router)
api_router.include_router(analyses.router)
api_router.include_router(portfolio.router)
api_router.include_router(matches.router)
