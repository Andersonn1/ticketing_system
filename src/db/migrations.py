"""Database migration utilities."""

from __future__ import annotations

import asyncio
import threading
import zlib
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Final

from alembic.config import Config
from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import command
from src.core.settings import get_settings

settings = get_settings()
_migration_lock = threading.Lock()
_advisory_lock_id: Final[int] = zlib.crc32(b"migration_lock")


def _build_alembic_config() -> Config:
    """Build an Alembic config preloaded with project runtime settings."""
    project_root = Path(__file__).resolve().parents[2]
    config = Config(Path(project_root, "alembic.ini").as_posix())
    config.set_main_option("script_location", Path(project_root, "alembic").as_posix())
    config.set_main_option("prepend_sys_path", Path(project_root).as_posix())
    config.attributes["configure_logger"] = False
    return config


@asynccontextmanager
async def _advisory_migration_lock():

    url = make_url(settings.database_url())
    if not url.drivername.startswith("postgresql"):
        yield
        return

    if url.drivername != "postgresql+asyncpg":
        url = url.set(drivername="postgresql+asyncpg")
    _engine: AsyncEngine | None = None
    try:
        _engine = create_async_engine(
            settings.database_url(),
            pool_pre_ping=True,
            future=True,
        )
        async with _engine.connect() as conn:
            conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
            await conn.execute(
                text("SELECT pg_advisory_lock(:lock_id)"),
                {"lock_id": _advisory_lock_id},
            )
            try:
                yield
            finally:
                await conn.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"),
                    {"lock_id": _advisory_lock_id},
                )
    finally:
        if _engine:
            await _engine.dispose()


def _upgrade_to_head(config: Config) -> None:
    """Run Alembic upgrade synchronously in a worker thread."""
    logger.info("Running Alembic Upgrade")
    command.upgrade(config, "head")
    logger.info("Running Alembic Upgrade Complete")


async def _assert_ticket_table(engine_url: str) -> None:
    """Ensure the primary ticket table exists after migrations."""
    engine: AsyncEngine = create_async_engine(engine_url, future=True)
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text(
                    """
                    SELECT to_regclass('public.ticket')
                """.strip()
                )
            )
            if result.scalar_one() is None:
                raise RuntimeError(
                    'Expected table "ticket" was not found after running migrations.'
                    " Verify alembic scripts are mounted correctly and migration history is valid."
                )
    finally:
        await engine.dispose()


async def run_startup_migrations() -> None:
    """Run Alembic migrations to the latest revision."""
    config = _build_alembic_config()
    with _migration_lock:
        async with _advisory_migration_lock():
            async with asyncio.TaskGroup() as tg:
                tg.create_task(asyncio.to_thread(_upgrade_to_head, config))
            await _assert_ticket_table(settings.database_url())
    logger.info("Validated runtime schema: ticket table is present.")
