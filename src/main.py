"""Application Entrypoint"""

from __future__ import annotations

from loguru import logger
from fastapi import Request
from nicegui import app, ui
from starlette.middleware.sessions import SessionMiddleware

from src.core.logging import configure_logging
from src.core.settings import get_settings
from src.db.migrations import run_startup_migrations
from src.db.session import close_db_connection
from src.pages import ai_page, home_page, manual_page

settings = get_settings()

# Application startup events
app.on_startup(configure_logging)


async def _run_startup_migrations() -> None:
    """Run migrations on startup and fail fast on errors."""
    logger.info("Running database migrations.")
    try:
        await run_startup_migrations()
    except Exception as exc:
        logger.exception("Startup migration failed: {}", exc)
        raise
    logger.success("Migrations complete.")


async def _close_db() -> None:
    """Clean up database connections."""
    await close_db_connection()


app.on_startup(_run_startup_migrations)
app.on_shutdown(_close_db)

app.add_middleware(
    SessionMiddleware, secret_key=settings.session_key.get_secret_value()
)


# Register Pages
@app.post("/dark_mode")
async def _post_dark_mode(request: Request) -> None:
    app.storage.browser["dark_mode"] = (await request.json()).get("value")


home_page.register()
manual_page.register()
ai_page.register()


@app.get("/status")
def _status():
    return "Ok"


ui.run(
    title=settings.app_name,
    favicon="🤖",
    reload=settings.app_env == "develop",
    host="0.0.0.0",
    port=8080,
)
