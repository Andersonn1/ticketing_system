"""Application dependency providers."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.settings import Settings
from src.core.settings import get_settings as _get_settings
from src.db.session import get_session as _get_session
from src.services import TicketService
from src.services.contracts import SupportsTriageLLMContract


def get_settings() -> Settings:
    """Return cached application settings."""
    return _get_settings()


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session for FastAPI dependencies."""
    async with _get_session() as session:
        yield session


def get_llm_client() -> SupportsTriageLLMContract:
    """Return the shared OpenAI client used by app-facing services."""
    from src.llm.openai_client import get_openai_client

    return get_openai_client()


def get_ticket_service() -> TicketService:
    """Return the ticket service used by UI pages."""
    return TicketService(
        session_provider=_get_session,
        llm_client=get_llm_client(),
    )
