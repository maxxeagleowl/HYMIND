"""Structured logger for HYMIND. Import get_logger() in every module."""

import logging
import os
from pathlib import Path

from rich.logging import RichHandler

_LOG_LEVEL_NAME: str = os.getenv("LOG_LEVEL", "INFO").upper()
_LOG_LEVEL: int = getattr(logging, _LOG_LEVEL_NAME, logging.INFO)
_LOG_DIR: Path = Path("logs")
_LOG_FILE: Path = _LOG_DIR / "hymind.log"


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger for the given module name.

    Console output uses Rich for readability.
    File output writes to logs/hymind.log at DEBUG level for full traceability.
    Calling this function multiple times with the same name is safe — handlers
    are only attached once.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # --- Console handler (Rich) ---
    console_handler = RichHandler(
        level=_LOG_LEVEL,
        rich_tracebacks=True,
        markup=False,
        show_path=False,
        log_time_format="[%H:%M:%S]",
    )
    logger.addHandler(console_handler)

    # --- File handler (always DEBUG for full audit trail) ---
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)
    except OSError as exc:
        logger.warning("Could not create log file at %s: %s", _LOG_FILE, exc)

    return logger
