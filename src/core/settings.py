"""Application Settings"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

VALID_LOG_LEVEL_NAMES = Literal[
    "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"
]
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

    app_name: str = Field(
        default="IT Support Demo", description="The name of the demo application"
    )
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
    log_file: str = Field(
        default="logs/app.log", description="Application log file path"
    )
    log_file_rotation: str = Field(
        default="3 days", description="Application log file retention period"
    )
    model: str = Field(..., description="The AI model that will be used")
    model_provider: str = Field(default=..., description="The AI model provider")
    model_provider_url: str = Field(
        default=..., description="The AI model provider's api endpoint"
    )
    model_provider_api_key: SecretStr = Field(
        default=SecretStr("Please provide a valid API key"),
        description="The API key to use to auth with the AI provider",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get an instance of the application settings"""
    return Settings()  # type: ignore
