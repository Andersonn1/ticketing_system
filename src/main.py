"""Application Entrypoint"""

from __future__ import annotations

from fastapi import Request
from nicegui import app, ui
from starlette.middleware.sessions import SessionMiddleware

from src.core.logging import configure_logging
from src.core.settings import get_settings
from src.pages import ai_page, home_page, manual_page

settings = get_settings()

# Application startup events
app.on_startup(configure_logging)

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
