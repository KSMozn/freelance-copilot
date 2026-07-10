from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.analytics_service import AnalyticsService
from app.application.services.application_service import ApplicationService
from app.application.services.auth_service import AuthService
from app.application.services.career_fitness_service import (
    CareerFitness,
    CareerFitnessService,
)
from app.application.services.citation_service import CitationService
from app.application.services.company_research_service import CompanyResearchService
from app.application.services.cv_ingest_service import CvIngestService
from app.application.services.email_otp_service import EmailOtpService
from app.application.services.gap_recommendation_service import (
    GapRecommendationService,
)
from app.application.services.job_analysis_service import JobAnalysisService
from app.application.services.job_confidence_service import JobConfidenceService
from app.application.services.job_import_service import JobImportService
from app.application.services.job_service import JobService
from app.application.services.knowledge_graph_service import KnowledgeGraphService
from app.application.services.linkedin_ingest_service import LinkedInIngestService
from app.application.services.market_signal_service import MarketSignalService
from app.application.services.match_report_service import MatchReportService
from app.application.services.output_generation_service import (
    OutputGenerationService,
)
from app.application.services.password_reset_service import PasswordResetService
from app.application.services.persona_profile_resolver import PersonaProfileResolver
from app.application.services.persona_service import PersonaService
from app.application.services.portfolio_matching_service import PortfolioMatchingService
from app.application.services.portfolio_service import PortfolioService
from app.application.services.portfolio_story_service import PortfolioStoryService
from app.application.services.proposal_generation_service import (
    ProposalGenerationService,
)
from app.application.services.proposal_review_service import ProposalReviewService
from app.application.services.refresh_token_manager import RefreshTokenManager
from app.application.services.repository_improvement_service import (
    RepositoryImprovementService,
)
from app.application.services.repository_matching_service import (
    RepositoryMatchingService,
)
from app.application.services.repository_scan_service import RepositoryScanService
from app.application.services.repository_service import RepositoryService
from app.application.services.repository_star_story_service import (
    RepositoryStarStoryService,
)
from app.application.services.resume_recommendation_service import (
    ResumeRecommendationService,
)
from app.application.services.resume_service import ResumeService
from app.application.services.scoring_service import ScoringService
from app.application.services.skill_catalog_service import SkillCatalogService
from app.application.services.skill_evidence_service import SkillEvidenceService
from app.core.config import Settings, get_settings
from app.core.database import AsyncSessionLocal
from app.domain.entities.match_report import MatchReport
from app.domain.entities.skill_catalog import SkillCatalogEntry
from app.domain.entities.user import User
from app.domain.exceptions import InvalidCredentialsError, NotFoundError
from app.domain.providers.ai_provider import AIProvider
from app.domain.providers.blob_store import BlobStore
from app.domain.providers.email_provider import EmailProvider
from app.domain.providers.embedding_provider import EmbeddingProvider
from app.infrastructure.ai.embedding_factory import build_embedding_provider
from app.infrastructure.ai.factory import build_ai_provider
from app.infrastructure.db.repositories.sqlalchemy_analysis_repository import (
    SQLAlchemyJobAnalysisRepository,
    SQLAlchemyOpportunityScoreRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_application_repository import (
    SQLAlchemyApplicationHistoryRepository,
    SQLAlchemyApplicationRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_email_otp_repository import (
    SQLAlchemyEmailOtpRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_embedding_repository import (
    SQLAlchemyEmbeddingRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_experience_repository import (
    SQLAlchemyExperienceRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_ingestion_repositories import (
    SQLAlchemyCvUploadRepository,
    SQLAlchemyLinkedInSnapshotRepository,
    SQLAlchemyUploadedFileRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_job_repository import SQLAlchemyJobRepository
from app.infrastructure.db.repositories.sqlalchemy_match_report_repository import (
    SQLAlchemyMatchReportRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_output_repository import (
    SQLAlchemyOutputRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_password_reset_token_repository import (
    SQLAlchemyPasswordResetTokenRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_persona_repository import (
    SQLAlchemyPersonaArchetypeRepository,
    SQLAlchemyPersonaRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_portfolio_repository import (
    SQLAlchemyPortfolioRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_proposal_repository import (
    SQLAlchemyProposalRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_repository_store import (
    SQLAlchemyRepositoryStore,
)
from app.infrastructure.db.repositories.sqlalchemy_resume_repository import (
    SQLAlchemyResumeRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_skill_catalog_repository import (
    SQLAlchemySkillCatalogRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.infrastructure.db.repositories.sqlalchemy_user_skill_repository import (
    SQLAlchemyUserSkillRepository,
)
from app.infrastructure.email.factory import build_email_provider
from app.infrastructure.email.mock_provider import read_dev_outbox
from app.infrastructure.github.github_client import GithubClient
from app.infrastructure.storage.factory import build_blob_store

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_email_provider(settings: SettingsDep) -> EmailProvider:
    return build_email_provider(settings)


# Callable (to, limit) -> captured dev emails, newest first. Kept behind DI so
# the dev-mailbox endpoint stays decoupled from the mock provider's storage.
DevOutboxReader = Callable[[str | None, int], list[dict[str, object]]]


def get_dev_outbox_reader() -> DevOutboxReader:
    return read_dev_outbox


DevOutboxReaderDep = Annotated[DevOutboxReader, Depends(get_dev_outbox_reader)]


def get_ai_provider(settings: SettingsDep) -> AIProvider:
    return build_ai_provider(settings)


def get_embedding_provider(settings: SettingsDep) -> EmbeddingProvider:
    return build_embedding_provider(settings)


def get_blob_store(settings: SettingsDep) -> BlobStore:
    return build_blob_store(settings)


# --- Phase B: knowledge graph services ------------------------------------


def get_skill_catalog_service(session: SessionDep) -> SkillCatalogService:
    return SkillCatalogService(SQLAlchemySkillCatalogRepository(session))


def get_knowledge_graph_service(
    session: SessionDep,
    skill_catalog: Annotated[SkillCatalogService, Depends(get_skill_catalog_service)],
) -> KnowledgeGraphService:
    return KnowledgeGraphService(
        skill_catalog=skill_catalog,
        user_skills=SQLAlchemyUserSkillRepository(session),
        experiences=SQLAlchemyExperienceRepository(session),
    )


def get_cv_ingest_service(
    session: SessionDep,
    ai_provider: Annotated[AIProvider, Depends(get_ai_provider)],
    kg: Annotated[KnowledgeGraphService, Depends(get_knowledge_graph_service)],
) -> CvIngestService:
    return CvIngestService(
        cv_uploads=SQLAlchemyCvUploadRepository(session),
        ai_provider=ai_provider,
        knowledge_graph=kg,
    )


def get_linkedin_ingest_service(
    session: SessionDep,
    ai_provider: Annotated[AIProvider, Depends(get_ai_provider)],
    kg: Annotated[KnowledgeGraphService, Depends(get_knowledge_graph_service)],
) -> LinkedInIngestService:
    return LinkedInIngestService(
        snapshots=SQLAlchemyLinkedInSnapshotRepository(session),
        files=SQLAlchemyUploadedFileRepository(session),
        ai_provider=ai_provider,
        knowledge_graph=kg,
    )


def get_persona_service(session: SessionDep) -> PersonaService:
    return PersonaService(
        personas=SQLAlchemyPersonaRepository(session),
        archetypes=SQLAlchemyPersonaArchetypeRepository(session),
    )


def get_persona_profile_resolver(session: SessionDep) -> PersonaProfileResolver:
    return PersonaProfileResolver(
        user_skills=SQLAlchemyUserSkillRepository(session),
        skill_catalog=SQLAlchemySkillCatalogRepository(session),
        personas=SQLAlchemyPersonaRepository(session),
        archetypes=SQLAlchemyPersonaArchetypeRepository(session),
    )


def get_email_otp_service(
    session: SessionDep,
    settings: SettingsDep,
    email_provider: Annotated[EmailProvider, Depends(get_email_provider)],
) -> EmailOtpService:
    return EmailOtpService(
        otp_repo=SQLAlchemyEmailOtpRepository(session),
        email_provider=email_provider,
        app_name=settings.app_name,
        from_address=settings.email_from_address,
        expires_minutes=settings.otp_expires_minutes,
        max_attempts=settings.otp_max_attempts,
        rate_limit_per_15min=settings.otp_rate_limit_per_15min,
    )


def get_auth_service(
    session: SessionDep,
    otp_service: Annotated[EmailOtpService, Depends(get_email_otp_service)],
    persona_service: Annotated[PersonaService, Depends(get_persona_service)],
) -> AuthService:
    return AuthService(
        SQLAlchemyUserRepository(session),
        otp_service,
        persona_service,
        RefreshTokenManager(SQLAlchemyRefreshTokenRepository(session)),
    )


def get_password_reset_service(
    session: SessionDep,
    settings: SettingsDep,
    email_provider: Annotated[EmailProvider, Depends(get_email_provider)],
) -> PasswordResetService:
    return PasswordResetService(
        user_repo=SQLAlchemyUserRepository(session),
        reset_repo=SQLAlchemyPasswordResetTokenRepository(session),
        refresh_tokens=RefreshTokenManager(SQLAlchemyRefreshTokenRepository(session)),
        email_provider=email_provider,
        app_name=settings.app_name,
        frontend_base_url=settings.frontend_base_url,
        expires_minutes=settings.password_reset_expires_minutes,
    )


PasswordResetServiceDep = Annotated[
    PasswordResetService, Depends(get_password_reset_service)
]


def get_job_service(session: SessionDep) -> JobService:
    return JobService(SQLAlchemyJobRepository(session))


async def get_scoring_service(
    user: "CurrentUser",
    resolver: Annotated[
        PersonaProfileResolver, Depends(get_persona_profile_resolver)
    ],
) -> ScoringService:
    """Build a ScoringService against the *active* persona's profile.

    Falls back to ``DEFAULT_FREELANCER_PROFILE`` for users with no personas
    and an empty pot (newly signed-up accounts pre-Phase-B-backfill, or any
    user before Phase C migrations).
    """
    profile = await resolver.load_for_user(user.id)
    return ScoringService(profile)


def get_job_import_service(
    session: SessionDep,
    ai_provider: Annotated[AIProvider, Depends(get_ai_provider)],
) -> JobImportService:
    return JobImportService(
        ai_provider=ai_provider,
        job_service=JobService(SQLAlchemyJobRepository(session)),
    )


def get_job_analysis_service(
    session: SessionDep,
    ai_provider: Annotated[AIProvider, Depends(get_ai_provider)],
    scoring: Annotated[ScoringService, Depends(get_scoring_service)],
) -> JobAnalysisService:
    return JobAnalysisService(
        job_repo=SQLAlchemyJobRepository(session),
        analysis_repo=SQLAlchemyJobAnalysisRepository(session),
        score_repo=SQLAlchemyOpportunityScoreRepository(session),
        ai_provider=ai_provider,
        scoring=scoring,
    )


def get_portfolio_service(
    session: SessionDep,
    embedding_provider: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
) -> PortfolioService:
    return PortfolioService(
        portfolio_repo=SQLAlchemyPortfolioRepository(session),
        embedding_repo=SQLAlchemyEmbeddingRepository(session),
        embedding_provider=embedding_provider,
    )


async def get_portfolio_matching_service(
    user: "CurrentUser",
    session: SessionDep,
    embedding_provider: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    resolver: Annotated[
        PersonaProfileResolver, Depends(get_persona_profile_resolver)
    ],
) -> PortfolioMatchingService:
    profile = await resolver.load_for_user(user.id)
    return PortfolioMatchingService(
        job_repo=SQLAlchemyJobRepository(session),
        portfolio_repo=SQLAlchemyPortfolioRepository(session),
        analysis_repo=SQLAlchemyJobAnalysisRepository(session),
        embedding_repo=SQLAlchemyEmbeddingRepository(session),
        portfolio_service=portfolio_service,
        embedding_provider=embedding_provider,
        profile=profile,
    )


def get_resume_service(
    session: SessionDep,
    embedding_provider: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
) -> ResumeService:
    return ResumeService(
        resume_repo=SQLAlchemyResumeRepository(session),
        embedding_repo=SQLAlchemyEmbeddingRepository(session),
        embedding_provider=embedding_provider,
    )


def get_resume_recommendation_service(
    session: SessionDep,
    embedding_provider: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
    resume_service: Annotated[ResumeService, Depends(get_resume_service)],
) -> ResumeRecommendationService:
    return ResumeRecommendationService(
        job_repo=SQLAlchemyJobRepository(session),
        resume_repo=SQLAlchemyResumeRepository(session),
        analysis_repo=SQLAlchemyJobAnalysisRepository(session),
        embedding_repo=SQLAlchemyEmbeddingRepository(session),
        resume_service=resume_service,
        embedding_provider=embedding_provider,
    )


def get_proposal_review_service() -> ProposalReviewService:
    return ProposalReviewService()


def get_proposal_generation_service(
    session: SessionDep,
    ai_provider: Annotated[AIProvider, Depends(get_ai_provider)],
    matching: Annotated[
        PortfolioMatchingService, Depends(get_portfolio_matching_service)
    ],
    recommendations: Annotated[
        ResumeRecommendationService, Depends(get_resume_recommendation_service)
    ],
    review: Annotated[ProposalReviewService, Depends(get_proposal_review_service)],
) -> ProposalGenerationService:
    return ProposalGenerationService(
        job_repo=SQLAlchemyJobRepository(session),
        analysis_repo=SQLAlchemyJobAnalysisRepository(session),
        score_repo=SQLAlchemyOpportunityScoreRepository(session),
        portfolio_repo=SQLAlchemyPortfolioRepository(session),
        portfolio_matching_service=matching,
        resume_recommendation_service=recommendations,
        proposal_repo=SQLAlchemyProposalRepository(session),
        ai_provider=ai_provider,
        review_service=review,
    )


def get_application_service(
    session: SessionDep,
    matching: Annotated[
        PortfolioMatchingService, Depends(get_portfolio_matching_service)
    ],
    recommendations: Annotated[
        ResumeRecommendationService, Depends(get_resume_recommendation_service)
    ],
) -> ApplicationService:
    return ApplicationService(
        application_repo=SQLAlchemyApplicationRepository(session),
        history_repo=SQLAlchemyApplicationHistoryRepository(session),
        job_repo=SQLAlchemyJobRepository(session),
        proposal_repo=SQLAlchemyProposalRepository(session),
        resume_repo=SQLAlchemyResumeRepository(session),
        portfolio_repo=SQLAlchemyPortfolioRepository(session),
        score_repo=SQLAlchemyOpportunityScoreRepository(session),
        portfolio_matching_service=matching,
        resume_recommendation_service=recommendations,
    )


def get_github_client(settings: SettingsDep) -> GithubClient:
    return GithubClient(token=settings.github_token, base_url=settings.github_api_base_url)


def get_repository_scan_service(
    ai_provider: Annotated[AIProvider, Depends(get_ai_provider)],
    github_client: Annotated[GithubClient, Depends(get_github_client)],
) -> RepositoryScanService:
    return RepositoryScanService(github_client=github_client, ai_provider=ai_provider)


def get_repository_service(
    session: SessionDep,
    embedding_provider: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
    scan_service: Annotated[RepositoryScanService, Depends(get_repository_scan_service)],
) -> RepositoryService:
    return RepositoryService(
        repository_store=SQLAlchemyRepositoryStore(session),
        embedding_repo=SQLAlchemyEmbeddingRepository(session),
        embedding_provider=embedding_provider,
        scan_service=scan_service,
    )


def get_company_research_service(
    session: SessionDep,
    ai_provider: Annotated[AIProvider, Depends(get_ai_provider)],
) -> CompanyResearchService:
    return CompanyResearchService(
        job_repo=SQLAlchemyJobRepository(session),
        ai_provider=ai_provider,
    )


def get_portfolio_story_service(
    session: SessionDep,
    ai_provider: Annotated[AIProvider, Depends(get_ai_provider)],
    portfolio_matching: Annotated[
        PortfolioMatchingService, Depends(get_portfolio_matching_service)
    ],
) -> PortfolioStoryService:
    return PortfolioStoryService(
        job_repo=SQLAlchemyJobRepository(session),
        analysis_repo=SQLAlchemyJobAnalysisRepository(session),
        portfolio_repo=SQLAlchemyPortfolioRepository(session),
        portfolio_matching=portfolio_matching,
        ai_provider=ai_provider,
    )


def get_skill_evidence_service(session: SessionDep) -> SkillEvidenceService:
    return SkillEvidenceService(
        job_repo=SQLAlchemyJobRepository(session),
        analysis_repo=SQLAlchemyJobAnalysisRepository(session),
        portfolio_repo=SQLAlchemyPortfolioRepository(session),
        resume_repo=SQLAlchemyResumeRepository(session),
        repository_store=SQLAlchemyRepositoryStore(session),
    )


def get_repository_matching_service(
    session: SessionDep,
    embedding_provider: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
    repository_service: Annotated[RepositoryService, Depends(get_repository_service)],
) -> RepositoryMatchingService:
    return RepositoryMatchingService(
        job_repo=SQLAlchemyJobRepository(session),
        repository_store=SQLAlchemyRepositoryStore(session),
        analysis_repo=SQLAlchemyJobAnalysisRepository(session),
        embedding_repo=SQLAlchemyEmbeddingRepository(session),
        repository_service=repository_service,
        embedding_provider=embedding_provider,
    )


def get_repository_star_story_service(
    session: SessionDep,
    ai_provider: Annotated[AIProvider, Depends(get_ai_provider)],
    repository_service: Annotated[RepositoryService, Depends(get_repository_service)],
) -> RepositoryStarStoryService:
    return RepositoryStarStoryService(
        repository_store=SQLAlchemyRepositoryStore(session),
        repository_service=repository_service,
        ai_provider=ai_provider,
    )


def get_repository_improvement_service(session: SessionDep) -> RepositoryImprovementService:
    return RepositoryImprovementService(
        job_repo=SQLAlchemyJobRepository(session),
        analysis_repo=SQLAlchemyJobAnalysisRepository(session),
        repository_store=SQLAlchemyRepositoryStore(session),
    )


def get_job_confidence_service(
    session: SessionDep,
    evidence: Annotated[SkillEvidenceService, Depends(get_skill_evidence_service)],
    portfolio_matching: Annotated[
        PortfolioMatchingService, Depends(get_portfolio_matching_service)
    ],
    repository_matching: Annotated[
        RepositoryMatchingService, Depends(get_repository_matching_service)
    ],
) -> JobConfidenceService:
    return JobConfidenceService(
        evidence_service=evidence,
        portfolio_matching=portfolio_matching,
        repository_matching=repository_matching,
        score_repo=SQLAlchemyOpportunityScoreRepository(session),
    )


def get_gap_recommendation_service() -> GapRecommendationService:
    return GapRecommendationService()


def get_match_report_service(
    session: SessionDep,
    confidence: Annotated[JobConfidenceService, Depends(get_job_confidence_service)],
    evidence: Annotated[SkillEvidenceService, Depends(get_skill_evidence_service)],
    recs: Annotated[GapRecommendationService, Depends(get_gap_recommendation_service)],
    resolver: Annotated[
        PersonaProfileResolver, Depends(get_persona_profile_resolver)
    ],
) -> MatchReportService:
    return MatchReportService(
        confidence=confidence,
        evidence=evidence,
        gap_recs=recs,
        resolver=resolver,
        jobs=SQLAlchemyJobRepository(session),
        personas=SQLAlchemyPersonaRepository(session),
        user_skills=SQLAlchemyUserSkillRepository(session),
        skill_catalog=SQLAlchemySkillCatalogRepository(session),
        reports=SQLAlchemyMatchReportRepository(session),
    )


def get_citation_service() -> CitationService:
    return CitationService()


def get_output_generation_service(
    session: SessionDep,
    ai_provider: Annotated[AIProvider, Depends(get_ai_provider)],
    resolver: Annotated[
        PersonaProfileResolver, Depends(get_persona_profile_resolver)
    ],
    citations: Annotated[CitationService, Depends(get_citation_service)],
) -> OutputGenerationService:
    return OutputGenerationService(
        ai_provider=ai_provider,
        outputs=SQLAlchemyOutputRepository(session),
        jobs=SQLAlchemyJobRepository(session),
        personas=SQLAlchemyPersonaRepository(session),
        resolver=resolver,
        user_skills=SQLAlchemyUserSkillRepository(session),
        skill_catalog=SQLAlchemySkillCatalogRepository(session),
        experiences=SQLAlchemyExperienceRepository(session),
        citations=citations,
    )


def get_market_signal_service() -> MarketSignalService:
    return MarketSignalService()


def get_career_fitness_service(
    market: Annotated[MarketSignalService, Depends(get_market_signal_service)],
) -> CareerFitnessService:
    return CareerFitnessService(market=market)


async def get_career_fitness_assembler(
    session: SessionDep,
    service: Annotated[
        CareerFitnessService, Depends(get_career_fitness_service)
    ],
) -> Callable[[UUID], Awaitable[CareerFitness]]:
    """Return a callable ``(user_id) -> CareerFitness`` bundling repo reads.

    Saves the endpoint from threading six repos through its signature;
    keeps the heavy lifting in one place so future caching / pagination
    has one seam to grow at.
    """
    from app.infrastructure.db.repositories.sqlalchemy_match_report_repository import (
        SQLAlchemyMatchReportRepository as _Reports,
    )

    analysis_repo = SQLAlchemyJobAnalysisRepository(session)
    application_repo = SQLAlchemyApplicationRepository(session)
    match_repo = _Reports(session)
    repository_store = SQLAlchemyRepositoryStore(session)
    user_skill_repo = SQLAlchemyUserSkillRepository(session)
    catalog_repo = SQLAlchemySkillCatalogRepository(session)

    async def _assemble(user_id: UUID) -> CareerFitness:
        analyses = await analysis_repo.list_for_user(user_id)
        # `list_for_analytics` returns a plain list without pagination —
        # exactly the shape we want for the dashboard aggregation.
        applications = await application_repo.list_for_analytics(user_id)

        # match_repo doesn't have a list-by-user (only by job). We
        # aggregate by iterating the user's analyses' jobs.
        match_reports: list[MatchReport] = []
        for a in analyses:
            match_reports.extend(
                await match_repo.list_for_job(user_id=user_id, job_id=a.job_id)
            )
        repositories = await repository_store.list_all_for_user(user_id)
        user_skills = await user_skill_repo.list_for_user(user_id)

        # Hydrate catalog rows we need so the service stays free of DB IO.
        catalog_by_id: dict[UUID, SkillCatalogEntry] = {}
        for row in user_skills:
            entry = await catalog_repo.get_by_id(row.skill_id)
            if entry is not None:
                catalog_by_id[row.skill_id] = entry

        return service.compose(
            user_id=user_id,
            analyses=analyses,
            applications=applications,
            match_reports=match_reports,
            repositories=repositories,
            user_skills=user_skills,
            catalog_by_id=catalog_by_id,
        )

    return _assemble


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
JobServiceDep = Annotated[JobService, Depends(get_job_service)]
RepositoryServiceDep = Annotated[RepositoryService, Depends(get_repository_service)]
RepositoryMatchingServiceDep = Annotated[
    RepositoryMatchingService, Depends(get_repository_matching_service)
]
SkillEvidenceServiceDep = Annotated[SkillEvidenceService, Depends(get_skill_evidence_service)]
CompanyResearchServiceDep = Annotated[
    CompanyResearchService, Depends(get_company_research_service)
]
PortfolioStoryServiceDep = Annotated[
    PortfolioStoryService, Depends(get_portfolio_story_service)
]
JobConfidenceServiceDep = Annotated[JobConfidenceService, Depends(get_job_confidence_service)]
RepositoryImprovementServiceDep = Annotated[
    RepositoryImprovementService, Depends(get_repository_improvement_service)
]
RepositoryStarStoryServiceDep = Annotated[
    RepositoryStarStoryService, Depends(get_repository_star_story_service)
]
JobImportServiceDep = Annotated[JobImportService, Depends(get_job_import_service)]
JobAnalysisServiceDep = Annotated[JobAnalysisService, Depends(get_job_analysis_service)]
PortfolioServiceDep = Annotated[PortfolioService, Depends(get_portfolio_service)]
PortfolioMatchingServiceDep = Annotated[
    PortfolioMatchingService, Depends(get_portfolio_matching_service)
]
ResumeServiceDep = Annotated[ResumeService, Depends(get_resume_service)]
ResumeRecommendationServiceDep = Annotated[
    ResumeRecommendationService, Depends(get_resume_recommendation_service)
]
ProposalGenerationServiceDep = Annotated[
    ProposalGenerationService, Depends(get_proposal_generation_service)
]
def get_analytics_service(session: SessionDep) -> AnalyticsService:
    return AnalyticsService(
        application_repo=SQLAlchemyApplicationRepository(session),
        history_repo=SQLAlchemyApplicationHistoryRepository(session),
    )


ApplicationServiceDep = Annotated[ApplicationService, Depends(get_application_service)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    auth: AuthServiceDep,
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return await auth.get_user_by_token(token)
    except (InvalidCredentialsError, NotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


CurrentUser = Annotated[User, Depends(get_current_user)]


# ---- Admin identity (Phase L.2) --------------------------------------
# admin_users is a completely separate identity space from users. Admin
# JWTs carry `pt=admin`. The two gates below enforce that split:
#   * get_current_user (above) already rejects admin tokens because
#     `get_admin_user_from_token` refuses to load a user_id if pt=admin.
#   * require_admin_user rejects user tokens for the same reason.


async def get_current_admin(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    session: SessionDep,
) -> "AdminUserEntity":
    from app.application.services.admin_auth_service import AdminAuthService
    from app.infrastructure.db.repositories.sqlalchemy_admin_user_repository import (
        SQLAlchemyAdminUserRepository,
    )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    svc = AdminAuthService(SQLAlchemyAdminUserRepository(session))
    try:
        admin = await svc.get_admin_by_token(token)
    except (InvalidCredentialsError, NotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is disabled",
        )
    return admin


# Forward-declare — the entity import here would create a cycle otherwise.
from app.domain.entities.admin_user import AdminUser as AdminUserEntity

CurrentAdmin = Annotated[AdminUserEntity, Depends(get_current_admin)]
