"""Application Entrypoint"""

from __future__ import annotations

from fastapi import Request
from loguru import logger
from nicegui import app, ui
from starlette.middleware.sessions import SessionMiddleware

from src.core.logging import configure_logging
from src.dependencies import get_settings
from src.db.migrations import run_startup_migrations
from src.db.seed import MOCK_DATA_PATH, run_seed
from src.db.session import close_db_connection
from src.pages import ai_service_page, home_page, manual_request_page, manual_service_page

settings = get_settings()


# Application startup events
async def _run_startup_tasks() -> None:
    """Run migrations, then seed data, and fail fast on errors."""
    configure_logging()

    try:
        logger.info("Running database migrations.")
        await run_startup_migrations()
    except Exception as exc:
        logger.exception("Startup migration failed: {}", exc)
        raise
    logger.success("Migrations complete.")

    logger.info("Running startup seed for mock ticket data.")
    try:
        result = await run_seed(MOCK_DATA_PATH)
    except Exception as exc:
        logger.exception("Startup seed failed: {}", exc)
        raise
    logger.success(
        """Seed complete:
         {} created,
           {} updated,
             {} skipped,
               {} payload(s) processed,
                 {} KB chunk(s) upserted.""",
        result.summary.created,
        result.summary.updated,
        result.summary.skipped,
        result.payloads_processed,
        result.kb_chunks_upserted,
    )


async def _close_db() -> None:
    """Clean up database connections."""
    await close_db_connection()


app.on_startup(_run_startup_tasks)
app.on_shutdown(_close_db)

app.add_middleware(SessionMiddleware, secret_key=settings.session_key.get_secret_value())


# Register Pages
@app.post("/dark_mode")
async def _post_dark_mode(request: Request) -> None:
    app.storage.browser["dark_mode"] = (await request.json()).get("value")


home_page.register()
manual_request_page.register()
manual_service_page.register()
ai_service_page.register()


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
