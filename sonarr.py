import httpx
from config import SONARR_URL, SONARR_API_KEY, logger


async def get_all_series(client: httpx.AsyncClient):
    """
    Fetch all series from Sonarr.
    """
    url = f"{SONARR_URL}/api/v3/series"
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.json()


async def get_series(client: httpx.AsyncClient, series_id: int):
    """
    Fetch a single series by ID from Sonarr.
    """
    url = f"{SONARR_URL}/api/v3/series/{series_id}"
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.json()


async def get_episodes_for_series(client: httpx.AsyncClient, series_id: int):
    """
    Fetch all episodes for a given series from Sonarr.
    """
    url = f"{SONARR_URL}/api/v3/episode?seriesId={series_id}"
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.json()


async def get_history_for_episode(client: httpx.AsyncClient, episode_id: int):
    """
    Fetch history for a given episode from Sonarr.
    """
    resp = await client.get(
        SONARR_URL + "/api/v3/history",
        params={"episodeId": episode_id, "pageSize": 100},
    )
    resp.raise_for_status()
    return resp.json()
