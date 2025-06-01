import logging
import os

import structlog
from dotenv import load_dotenv

structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))


def wrap_async(logger) -> structlog.stdlib.AsyncBoundLogger:
    return structlog.wrap_logger(
        logger, wrapper_class=structlog.stdlib.AsyncBoundLogger
    )


def get_async_logger() -> structlog.stdlib.AsyncBoundLogger:
    return wrap_async(
        structlog.get_logger(),
    )


logger: structlog.stdlib.AsyncBoundLogger = structlog.getLogger()


def getenv(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"{key} must be set in the .env file.")
    return value


load_dotenv()
SONARR_URL: str = getenv("SONARR_URL")
SONARR_API_KEY: str = getenv("SONARR_API_KEY")
AUTHELIA_URL: str = getenv("AUTHELIA_URL")
