"""Application Settings"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

VALID_LOG_LEVEL_NAMES = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]
VALID_LOG_LEVEL_INTS = Literal[50, 40, 30, 20, 10, 0]


class Settings(BaseSettings):
    """Applications Settings"""

    model_config = SettingsConfigDict(
        frozen=True,
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    app_name: str = Field(default="IT Support Demo", description="The name of the demo application")
    app_env: Literal["develop", "staging", "production"] = Field(
        default="develop", description="The environments the app is running in"
    )
    session_key: SecretStr = Field(
        default=SecretStr("demo-secret-key"),
        description="The session key, defaults to a dummy demo value never use in prod",
    )
    log_level: VALID_LOG_LEVEL_NAMES | VALID_LOG_LEVEL_INTS = Field(
        default="DEBUG", description="Application logging level"
    )
    log_file: str = Field(default="logs/app.log", description="Application log file path")
    log_file_rotation: str = Field(default="3 days", description="Application log file retention period")
    reindex: bool = Field(default=False, description="Where or not to reindex data")
    openai_chat_model: str = Field(..., description="The OpenAI model that will be used")
    openai_embedding_model: str = Field(
        ...,
        description="The OpenAI embedding model that will be used",
    )
    openai_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="The API key to use to auth with OpenAI",
    )
    openai_timeout_seconds: float = Field(
        default=60,
        description="Timeout in seconds for AI provider requests",
    )
    openai_max_retries: int = Field(
        default=2,
        description="Maximum retry count for AI provider requests",
    )
    db_name: str = Field(..., description="The postgres database name")
    db_user: str = Field(..., description="The postgres database user")
    db_host: str = Field(default="localhost", description="The postgres host")
    db_password: SecretStr = Field(..., description="The postgres database password")
    db_port: int = Field(default=5432, description="The postgres database port")

    def database_url(self) -> str:
        """Build the async SQLAlchemy connection URL for PostgreSQL."""
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            path=self.db_name,
        ).unicode_string()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get an instance of the application settings"""
    return Settings()  # type: ignore
