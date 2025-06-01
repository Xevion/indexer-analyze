from anyio import run
import os
from collections import defaultdict
from typing import Dict

import structlog

from auth import authelia_login
from config import get_async_logger
from format import ellipsis
import anyio
from collections import Counter
from sonarr import (
    get_all_series,
    get_episodes_for_series,
    get_history_for_episode,
    get_series,
    set_concurrency_limit,
)

logger: structlog.stdlib.AsyncBoundLogger = get_async_logger()


async def process_series(client, series_id: int) -> Dict[str, int]:
    """
    For a given series, count the number of files per indexer by analyzing episode history.
    Returns a dictionary mapping indexer names to file counts.
    """
    series = await get_series(client, series_id)
    episodes = await get_episodes_for_series(client, series_id)
    indexer_counts: Dict[str, int] = defaultdict(lambda: 0)

    # Process episodes in parallel for this series
    async def process_episode(ep):
        nonlocal indexer_counts
        # Skip episodes without files
        if not ep.get("hasFile", False):
            return
        indexer = "unknown"
        episode_detail = f"{ellipsis(series['title'], 12)} S{ep['seasonNumber']:02}E{ep['episodeNumber']:02} - {ellipsis(ep.get('title', 'Unknown'), 18)}"
        try:
            history = await get_history_for_episode(client, ep["id"])
        except Exception as e:
            if (
                hasattr(e, "response")
                and getattr(e.response, "status_code", None) == 404
            ):
                await logger.warning(
                    "History not found for episode (404)",
                    episode_id=ep["id"],
                    episode=episode_detail,
                )
                return
            else:
                await logger.error(
                    "Error fetching history for episode",
                    episode_id=ep["id"],
                    episode=episode_detail,
                    error=str(e),
                )
                return
        target_file_id = ep.get("episodeFileId")
        if not target_file_id:
            await logger.error(
                "No episode file for episode",
                episode_id=ep["id"],
                episode=episode_detail,
            )
            return

        # Find the 'downloadFolderImported' event with the matching data.fileId
        def is_import_event(event: Dict, file_id: int) -> bool:
            return event.get("eventType") == "downloadFolderImported" and event.get(
                "data", {}
            ).get("fileId") == str(file_id)

        import_event = next(
            (
                event
                for event in history["records"]
                if is_import_event(event, target_file_id)
            ),
            None,
        )
        if not import_event:
            await logger.debug(
                "No import event found for episode file",
                episode_id=ep["id"],
                episode=episode_detail,
                target_file_id=target_file_id,
            )
            return

        # Acquire the event's downloadId
        download_id = import_event.get("downloadId")
        if not download_id:
            await logger.error(
                "No downloadId found in import event",
                episode_id=ep["id"],
                episode=episode_detail,
                target_file_id=target_file_id,
            )
            return

        # Find the 'grabbed' event with the matching downloadId
        def is_grabbed_event(event: Dict, download_id: str) -> bool:
            return (
                event.get("eventType") == "grabbed"
                and event.get("downloadId") == download_id
            )

        grabbed_event = next(
            (
                event
                for event in history["records"]
                if is_grabbed_event(event, download_id)
            ),
            None,
        )
        if not grabbed_event:
            await logger.debug(
                "No 'grabbed' event found",
                episode_id=ep["id"],
                download_id=ellipsis(download_id, 20),
                episode=episode_detail,
            )
            return

        # Extract the indexer from the 'grabbed' event
        indexer = grabbed_event.get("data", {}).get("indexer")
        if not indexer:
            await logger.warning(
                "No indexer provided in 'grabbed' event",
                episode_id=ep["id"],
                episode=episode_detail,
                download_id=ellipsis(download_id, 20),
            )

            indexer = "unknown"

            # Normalize indexer names by removing the "(Prowlarr)" suffix
            indexer = indexer[:-11] if indexer.endswith("(Prowlarr)") else indexer

        indexer_counts[indexer] += 1

    async with anyio.create_task_group() as tg:
        for ep in episodes:
            tg.start_soon(process_episode, ep)

    return indexer_counts


async def main():
    """
    Entrypoint: Authenticates with Authelia, fetches all Sonarr series, and logs per-series indexer statistics.
    """
    username = os.getenv("AUTHELIA_USERNAME")
    password = os.getenv("AUTHELIA_PASSWORD")

    if not username or not password:
        await logger.critical(
            "Missing Authelia credentials",
            AUTHELIA_USERNAME=username,
            AUTHELIA_PASSWORD=bool(password),
        )
        raise Exception(
            "AUTHELIA_USERNAME and AUTHELIA_PASSWORD must be set in the .env file."
        )

    set_concurrency_limit(25)  # Set the max number of concurrent Sonarr API requests

    # Request counter setup
    request_counter = {"count": 0, "active": 0}
    counter_lock = anyio.Lock()

    async def count_requests(request):
        async with counter_lock:
            request_counter["count"] += 1
            request_counter["active"] += 1

    async def count_responses(response):
        async with counter_lock:
            request_counter["active"] -= 1

    # Attach the event hooks to the client
    client = await authelia_login(username, password)
    if hasattr(client, "event_hooks"):
        client.event_hooks.setdefault("request", []).append(count_requests)
        client.event_hooks.setdefault("response", []).append(count_responses)

    series_list = await get_all_series(client)

    total_indexer_counts = Counter()

    async def process_and_log(series):
        indexer_counts = await process_series(client, series["id"])
        if any(indexer_counts.keys()):
            await logger.debug(
                "Processed series",
                series_title=series["title"],
                series_id=series["id"],
                indexers=dict(indexer_counts),
            )
            total_indexer_counts.update(indexer_counts)

    async def print_rps(interval=3):
        while True:
            await anyio.sleep(interval)
            async with counter_lock:
                rps = request_counter["count"] / interval
                active = request_counter["active"]
                request_counter["count"] = 0
            await logger.info(
                "Requests per second and active requests",
                rps=rps,
                active_requests=active,
                interval=interval,
            )

    async with anyio.create_task_group() as tg:
        tg.start_soon(print_rps, 3)
        for series in series_list:
            tg.start_soon(process_and_log, series)

    await logger.info(
        "Total indexer counts across all series",
        indexers=dict(total_indexer_counts),
    )


if __name__ == "__main__":
    run(main)
