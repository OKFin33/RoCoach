from __future__ import annotations

import logging


LOGGER_NAME = "roco.api"


def get_api_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger


def summarize_exception(exc: BaseException) -> str:
    return exc.__class__.__name__
