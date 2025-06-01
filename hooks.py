import httpx
import structlog

from config import SONARR_API_KEY, SONARR_URL, get_async_logger

logger: structlog.stdlib.AsyncBoundLogger = get_async_logger()


async def add_sonarr_api_key(request: httpx.Request) -> None:
    """
    Event hook to inject the Sonarr API key into requests to the Sonarr domain and /api path.
    """
    if SONARR_URL and request.url.host in SONARR_URL and "/api" in request.url.path:
        request.headers["X-Api-Key"] = SONARR_API_KEY
