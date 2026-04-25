from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from backend.config import runtime_paths


def configure_logging(level: str = "INFO") -> None:
    paths = runtime_paths()
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        paths.backend_log,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(numeric_level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

