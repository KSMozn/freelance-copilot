from app.infrastructure.db.models.application import (
    Application,
    ApplicationHistory,
    ApplicationPortfolio,
)
from app.infrastructure.db.models.client import Client
from app.infrastructure.db.models.email_otp_code import EmailOtpCode
from app.infrastructure.db.models.embedding import Embedding
from app.infrastructure.db.models.experience import (
    Experience,
    ExperienceAchievement,
    ExperienceSkill,
)
from app.infrastructure.db.models.job import Job, JobSkill
from app.infrastructure.db.models.job_analysis import JobAnalysis
from app.infrastructure.db.models.opportunity_score import OpportunityScore
from app.infrastructure.db.models.persona import Persona, PersonaArchetype
from app.infrastructure.db.models.portfolio import Portfolio, PortfolioSkill
from app.infrastructure.db.models.project import (
    Project,
    ProjectAchievement,
    ProjectSkill,
)
from app.infrastructure.db.models.proposal import Proposal
from app.infrastructure.db.models.repository import Repository
from app.infrastructure.db.models.resume import Resume, ResumeSkill
from app.infrastructure.db.models.skill import Skill
from app.infrastructure.db.models.skill_catalog import SkillCatalog
from app.infrastructure.db.models.tag import Tag
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.user_skill import UserSkill

__all__ = [
    "Application",
    "ApplicationHistory",
    "ApplicationPortfolio",
    "Client",
    "EmailOtpCode",
    "Embedding",
    "Experience",
    "ExperienceAchievement",
    "ExperienceSkill",
    "Job",
    "JobAnalysis",
    "JobSkill",
    "OpportunityScore",
    "Persona",
    "PersonaArchetype",
    "Portfolio",
    "PortfolioSkill",
    "Project",
    "ProjectAchievement",
    "ProjectSkill",
    "Proposal",
    "Repository",
    "Resume",
    "ResumeSkill",
    "Skill",
    "SkillCatalog",
    "Tag",
    "User",
    "UserSkill",
]
