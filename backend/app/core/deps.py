from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.auth_service import AuthService
from app.application.services.job_analysis_service import JobAnalysisService
from app.application.services.job_service import JobService
from app.application.services.scoring_service import ScoringService
from app.core.config import Settings, get_settings
from app.core.database import AsyncSessionLocal
from app.domain.entities.user import User
from app.domain.exceptions import InvalidCredentialsError, NotFoundError
from app.domain.profiles.freelancer_profile import DEFAULT_FREELANCER_PROFILE
from app.domain.providers.ai_provider import AIProvider
from app.infrastructure.ai.factory import build_ai_provider
from app.infrastructure.db.repositories.sqlalchemy_analysis_repository import (
    SQLAlchemyJobAnalysisRepository,
    SQLAlchemyOpportunityScoreRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_job_repository import SQLAlchemyJobRepository
from app.infrastructure.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository

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


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(SQLAlchemyUserRepository(session))


def get_job_service(session: SessionDep) -> JobService:
    return JobService(SQLAlchemyJobRepository(session))


def get_ai_provider(settings: SettingsDep) -> AIProvider:
    return build_ai_provider(settings)


def get_scoring_service() -> ScoringService:
    return ScoringService(DEFAULT_FREELANCER_PROFILE)


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


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
JobServiceDep = Annotated[JobService, Depends(get_job_service)]
JobAnalysisServiceDep = Annotated[JobAnalysisService, Depends(get_job_analysis_service)]


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
