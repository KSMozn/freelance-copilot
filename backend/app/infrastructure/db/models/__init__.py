from app.infrastructure.db.models.application import (
    Application,
    ApplicationHistory,
    ApplicationPortfolio,
)
from app.infrastructure.db.models.client import Client
from app.infrastructure.db.models.embedding import Embedding
from app.infrastructure.db.models.job import Job, JobSkill
from app.infrastructure.db.models.job_analysis import JobAnalysis
from app.infrastructure.db.models.opportunity_score import OpportunityScore
from app.infrastructure.db.models.portfolio import Portfolio, PortfolioSkill
from app.infrastructure.db.models.proposal import Proposal
from app.infrastructure.db.models.resume import Resume, ResumeSkill
from app.infrastructure.db.models.skill import Skill
from app.infrastructure.db.models.tag import Tag
from app.infrastructure.db.models.user import User

__all__ = [
    "Application",
    "ApplicationHistory",
    "ApplicationPortfolio",
    "Client",
    "Embedding",
    "Job",
    "JobAnalysis",
    "JobSkill",
    "OpportunityScore",
    "Portfolio",
    "PortfolioSkill",
    "Proposal",
    "Resume",
    "ResumeSkill",
    "Skill",
    "Tag",
    "User",
]
