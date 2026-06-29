from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "staging", "production", "test"] = "development"

    postgres_user: str = "upwork"
    postgres_password: str = "upwork"
    postgres_db: str = "upwork_intel"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    secret_key: str = Field(min_length=16)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14

    cors_origins: str = "http://localhost:5173"

    ai_provider: Literal["openai", "claude", "mock"] = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    # Override to point the OpenAI-compatible provider at Groq, Together,
    # Ollama, etc. Defaults to OpenAI's own endpoint.
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str | None = None
    claude_model: str = "claude-sonnet-4-6"

    embedding_provider: Literal["openai", "mock"] = "mock"
    openai_embedding_model: str = "text-embedding-3-small"

    github_token: str | None = None
    github_api_base_url: str = "https://api.github.com"

    email_provider: Literal["mock", "resend"] = "mock"
    resend_api_key: str | None = None
    email_from_address: str = "no-reply@example.com"
    email_from_name: str | None = "Freelance Copilot"
    app_name: str = "Freelance Copilot"
    otp_expires_minutes: int = 10
    otp_max_attempts: int = 5
    otp_rate_limit_per_15min: int = 3
    frontend_base_url: str = "http://localhost:5173"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_database_url(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
