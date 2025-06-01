import httpx
from config import SONARR_URL, SONARR_API_KEY, logger


# Add a global semaphore for concurrency limiting
semaphore = None


async def with_limit(coro):
    global semaphore
    if semaphore is None:
        raise RuntimeError(
            "Semaphore not initialized. Call set_concurrency_limit first."
        )
    async with semaphore:
        return await coro


def set_concurrency_limit(limit: int):
    global semaphore
    import anyio

    semaphore = anyio.Semaphore(limit)


async def get_all_series(client: httpx.AsyncClient):
    resp = await with_limit(client.get(f"{SONARR_URL}/api/v3/series"))
    resp.raise_for_status()
    return resp.json()


async def get_series(client: httpx.AsyncClient, series_id: int):
    resp = await with_limit(client.get(f"{SONARR_URL}/api/v3/series/{series_id}"))
    resp.raise_for_status()
    return resp.json()


async def get_episodes_for_series(client: httpx.AsyncClient, series_id: int):
    resp = await with_limit(
        client.get(f"{SONARR_URL}/api/v3/episode?seriesId={series_id}")
    )
    resp.raise_for_status()
    return resp.json()


async def get_history_for_episode(client: httpx.AsyncClient, episode_id: int):
    resp = await with_limit(
        client.get(
            SONARR_URL + "/api/v3/history",
            params={"episodeId": episode_id, "pageSize": 100},
        )
    )
    resp.raise_for_status()
    return resp.json()
