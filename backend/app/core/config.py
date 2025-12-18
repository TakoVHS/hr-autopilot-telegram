from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment/.env."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "HR Autopilot API"
    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    app_version: str | None = Field(default=None, alias="APP_VERSION")
    debug: bool = True
    api_prefix: str = "/api"
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@postgres:5432/hr_autopilot",
        alias="DATABASE_URL",
    )
    webhook_secret: str | None = Field(default=None, alias="WEBHOOK_SECRET")
    backend_public_url: str | None = Field(default=None, alias="BACKEND_PUBLIC_URL")
    telegram_bot_token: str | None = Field(
        default=None, validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN", "BOT_TOKEN")
    )
    telegram_admin_chat_id: str | None = Field(
        default=None, alias="TELEGRAM_ADMIN_CHAT_ID"
    )
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    hr_agent_id: str | None = Field(default=None, alias="HR_AGENT_ID")
    internal_api_token: str | None = Field(default=None, alias="INTERNAL_API_TOKEN")
    commit_sha: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "GIT_COMMIT_SHA", "COMMIT_SHA", "RENDER_GIT_COMMIT"
        ),
    )


def _build_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


@lru_cache
def get_settings() -> Settings:
    return _build_settings()


settings = get_settings()
