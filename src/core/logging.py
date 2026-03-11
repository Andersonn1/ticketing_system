"""Logging Configuration"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from src.dependencies import get_settings

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

_FALLBACK_LOG_FILE = Path("logs") / "app.log"


def configure_logging() -> None:
    """Configure Application Logging"""
    settings = get_settings()

    logger.remove()

    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=LOG_FORMAT,
        colorize=True,
    )

    for log_path in (settings.log_file, str(_FALLBACK_LOG_FILE)):
        try:
            output_path = Path(log_path).expanduser()
            if output_path.parent != Path("."):
                output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.add(
                output_path,
                rotation=settings.log_file_rotation,
                level=settings.log_level,
                format=LOG_FORMAT,
                colorize=False,
            )
            break
        except OSError as exc:
            logger.warning("Unable to configure file logging for {}: {}", log_path, exc)
