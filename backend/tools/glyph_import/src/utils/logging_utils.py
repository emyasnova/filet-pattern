"""Logging helpers for the glyph import CLI."""

from __future__ import annotations

import logging
from pathlib import Path


LOGGER_NAME = "glyph_import"


def setup_logging(log_file: Path, *, debug: bool = False) -> logging.Logger:
    """Configure file logging for the CLI process."""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger
