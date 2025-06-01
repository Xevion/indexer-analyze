import httpx
import structlog
from config import AUTHELIA_URL, get_async_logger
from hooks import add_sonarr_api_key

logger: structlog.stdlib.AsyncBoundLogger = get_async_logger()


async def authelia_login(username: str, password: str) -> httpx.AsyncClient:
    """
    Perform Authelia login and return an authenticated httpx.AsyncClient with Sonarr API key added.
    """
    client = httpx.AsyncClient(
        event_hooks={"request": [add_sonarr_api_key]},
        http2=True,
        limits=httpx.Limits(
            keepalive_expiry=60, max_connections=200, max_keepalive_connections=30
        ),
    )

    login_url = f"{AUTHELIA_URL}/api/firstfactor"
    payload = {"username": username, "password": password}
    resp = await client.post(login_url, json=payload)
    resp.raise_for_status()

    # If login is successful, cookies are set in the client
    await logger.info("Authelia login successful", username=username)

    return client
