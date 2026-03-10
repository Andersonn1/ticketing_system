"""Database session helpers for async SQLAlchemy."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.settings import get_settings

_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def _initialize_session_maker() -> None:
    """Initialize async SQLAlchemy engine and session factory once."""
    global _engine, _session_maker
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url(),
            pool_pre_ping=True,
            future=True,
        )
        _session_maker = async_sessionmaker(
            bind=_engine,
            expire_on_commit=False,
            autoflush=False,
        )


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Provide an async SQLAlchemy session."""
    _initialize_session_maker()
    if _session_maker is None:
        raise RuntimeError("Database session maker was not initialized")

    async with _session_maker() as session:
        yield session


async def close_db_connection() -> None:
    """Dispose the SQLAlchemy engine and clear in-memory references."""
    global _engine, _session_maker

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_maker = None
