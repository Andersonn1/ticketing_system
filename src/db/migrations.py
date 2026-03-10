"""Database migration utilities."""

from __future__ import annotations

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

from src.core.settings import get_settings


def _build_alembic_config() -> Config:
    """Build an Alembic config preloaded with project runtime settings."""
    project_root = Path(__file__).resolve().parents[1]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", get_settings().database_url())
    config.set_main_option("script_location", str(project_root / "alembic"))
    return config


def _upgrade_to_head(config: Config) -> None:
    """Run Alembic upgrade synchronously in a worker thread."""
    command.upgrade(config, "head")


async def run_startup_migrations() -> None:
    """Run Alembic migrations to the latest revision."""
    await asyncio.to_thread(_upgrade_to_head, _build_alembic_config())
