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
from app.infrastructure.db.models.ingestion import (
    Certificate,
    ContentItem,
    CvUpload,
    LinkedInSnapshot,
    UploadedFile,
)
from app.infrastructure.db.models.job import Job, JobSkill
from app.infrastructure.db.models.job_analysis import JobAnalysis
from app.infrastructure.db.models.match_report import MatchReport
from app.infrastructure.db.models.opportunity_score import OpportunityScore
from app.infrastructure.db.models.output import Output
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
from app.infrastructure.db.models.student_profile import (
    StudentProfile,
    StudentProfileEntry,
)
from app.infrastructure.db.models.tag import Tag
from app.infrastructure.db.models.tracker import (
    FollowUpReminder,
    InterviewEvent,
    RecruiterInteraction,
)
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.user_skill import UserSkill

__all__ = [
    "Application",
    "ApplicationHistory",
    "ApplicationPortfolio",
    "Certificate",
    "Client",
    "ContentItem",
    "CvUpload",
    "EmailOtpCode",
    "Embedding",
    "Experience",
    "ExperienceAchievement",
    "ExperienceSkill",
    "FollowUpReminder",
    "InterviewEvent",
    "Job",
    "JobAnalysis",
    "JobSkill",
    "LinkedInSnapshot",
    "MatchReport",
    "OpportunityScore",
    "Output",
    "Persona",
    "PersonaArchetype",
    "Portfolio",
    "PortfolioSkill",
    "Project",
    "ProjectAchievement",
    "ProjectSkill",
    "Proposal",
    "RecruiterInteraction",
    "Repository",
    "Resume",
    "ResumeSkill",
    "Skill",
    "SkillCatalog",
    "StudentProfile",
    "StudentProfileEntry",
    "Tag",
    "UploadedFile",
    "User",
    "UserSkill",
]
