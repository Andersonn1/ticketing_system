"""Application dependency providers."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.settings import Settings
from src.core.settings import get_settings as _get_settings
from src.db.session import get_session as _get_session
from src.llm.ollama_client import OllamaClient
from src.llm.ollama_client import get_ollama_client as _get_ollama_client
from src.services import TicketService


def get_settings() -> Settings:
    """Return cached application settings."""
    return _get_settings()


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session for FastAPI dependencies."""
    async with _get_session() as session:
        yield session


def get_ollama_client() -> OllamaClient:
    """Return the shared Ollama client used by app-facing services."""
    return _get_ollama_client()


def get_ticket_service() -> TicketService:
    """Return the ticket service used by UI pages."""
    return TicketService(
        session_provider=_get_session,
        ollama_client=get_ollama_client(),
    )
