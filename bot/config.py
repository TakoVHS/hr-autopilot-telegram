from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    telegram_token: str = Field(
        ..., validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN", "BOT_TOKEN")
    )
    telegram_admin_chat_id: str | None = Field(
        default=None, alias="TELEGRAM_ADMIN_CHAT_ID"
    )
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    hr_agent_id: str = Field(..., alias="HR_AGENT_ID")
    backend_url: str = Field(..., alias="BACKEND_URL")
    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    app_version: str | None = Field(default=None, alias="APP_VERSION")
    commit_sha: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "GIT_COMMIT_SHA", "COMMIT_SHA", "RENDER_GIT_COMMIT"
        ),
    )


settings = Settings()
