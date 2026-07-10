from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Signing keys that ship in the repo / CI for local use. None of these may
# sign real tokens — the validator below refuses to boot on them outside dev.
_PLACEHOLDER_SECRETS = frozenset(
    {
        "change-me",
        "change-me-in-production-this-is-a-dev-only-key",
        "ci-secret-key-please-change",
    }
)


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
    # Admin "view as user" tokens are short-lived and non-refreshable, so an
    # abandoned impersonation session self-expires quickly instead of lingering
    # for the normal 14-day refresh window.
    impersonation_token_expire_minutes: int = 30

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

    # Blob storage for student photos + ingestion uploads.
    # `local` writes to `uploads_dir` (good for dev / docker-compose).
    # `gcs` writes to the GCS bucket `gcs_uploads_bucket` (used by Cloud Run).
    blob_store: Literal["local", "gcs"] = "local"
    uploads_dir: str = "var/uploads"
    gcs_uploads_bucket: str | None = None

    github_token: str | None = None
    github_api_base_url: str = "https://api.github.com"

    email_provider: Literal["mock", "resend"] = "mock"
    resend_api_key: str | None = None
    email_from_address: str = "no-reply@example.com"
    # Rebranded to Careero — students see this in email subjects, from names,
    # and OTP body headers. PersonaArmory is the parent company (surfaces only
    # on the admin panel + wizard footer).
    email_from_name: str | None = "Careero"
    app_name: str = "Careero"
    otp_expires_minutes: int = 10
    otp_max_attempts: int = 5
    otp_rate_limit_per_15min: int = 3
    # Forgot-password links are single-use and short-lived; 15-30 min is the
    # accepted window for email-delivered reset tokens.
    password_reset_expires_minutes: int = 30
    frontend_base_url: str = "http://localhost:5173"
    # Shared secret Cloud Scheduler sends in `X-Task-Secret` when kicking
    # the daily-report endpoint. Left None in dev so local invocations
    # skip the check; in prod this is mounted from Secret Manager and
    # the endpoint 401s on mismatch.
    report_task_secret: str | None = None
    admin_base_url: str = "http://localhost:5173"

    @model_validator(mode="after")
    def _harden_for_deployed_envs(self) -> "Settings":
        """Fail closed on insecure config in staging/production.

        Dev/test keep their conveniences (placeholder key, mock email). The
        moment `environment` is staging or production we refuse to start on a
        known/weak signing key or the mock email provider (which logs OTP
        codes) — a missing Secret Manager mount becomes a boot failure, not a
        silent security hole.
        """
        # The API always sends `Access-Control-Allow-Credentials: true`, which
        # is incompatible with a wildcard origin (the browser rejects it and,
        # worse, Starlette would reflect the caller's origin). Refuse `*` in
        # every env so it can't be introduced by a stray env var.
        if "*" in self.cors_origin_list:
            raise ValueError(
                "CORS_ORIGINS cannot contain '*' while credentials are allowed"
            )

        if self.environment in ("staging", "production"):
            if self.secret_key in _PLACEHOLDER_SECRETS or len(self.secret_key) < 32:
                raise ValueError(
                    "SECRET_KEY must be a strong, non-placeholder value "
                    "(>=32 chars) in staging/production"
                )
            if self.email_provider == "mock":
                raise ValueError(
                    "EMAIL_PROVIDER must not be 'mock' in staging/production "
                    "(the mock provider logs OTP codes)"
                )
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        return _build_database_url(self, scheme="postgresql+asyncpg")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_database_url(self) -> str:
        return _build_database_url(self, scheme="postgresql+psycopg")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


def _build_database_url(settings: "Settings", *, scheme: str) -> str:
    """Build a Postgres DSN that supports both TCP (local docker, etc.) and
    Unix-socket (Cloud SQL via Cloud Run) connections.

    Cloud Run mounts the Cloud SQL Auth Proxy socket under
    `/cloudsql/PROJECT:REGION:INSTANCE` when the service is configured with
    `--add-cloudsql-instances`. Driver convention: pass that path as the
    `host` query parameter while leaving the URL host empty.
    """
    from urllib.parse import quote_plus

    user = quote_plus(settings.postgres_user)
    pwd = quote_plus(settings.postgres_password)
    db = settings.postgres_db
    host = settings.postgres_host

    if host.startswith("/"):
        return f"{scheme}://{user}:{pwd}@/{db}?host={host}"
    return f"{scheme}://{user}:{pwd}@{host}:{settings.postgres_port}/{db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
