"""Логирование мода. Пишет только диагностику, без персональных данных игрока."""

from __future__ import annotations

import logging
from pathlib import Path

ROOT_LOGGER_NAME = "after_dark"
_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")


def setup_logging(level: str = "INFO", log_file: Path | None = None) -> logging.Logger:
    """Настроить корневой логгер мода. Повторные вызовы не дублируют обработчики."""
    root = logging.getLogger(ROOT_LOGGER_NAME)
    root.setLevel(getattr(logging, level, logging.INFO))
    root.propagate = False
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()
    handler: logging.Handler
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_file, encoding="utf-8")
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_FORMAT))
    root.addHandler(handler)
    return root
