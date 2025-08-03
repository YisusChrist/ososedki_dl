"""Common functions for crawlers."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from aiohttp import ClientResponseError
from bs4 import BeautifulSoup
from core_helpers.logs import logger
from rich import print
from rich.progress import Progress, TaskID

from ..download import SessionType, download_and_save_media, fetch
from ..utils import get_final_path

# region Context class


@dataclass
class CrawlerContext:
    session: SessionType
    download_path: Path
    progress: Progress
    task: TaskID


# endregion Context class

# region Fetching functions


async def fetch_soup(session: SessionType, url: str) -> BeautifulSoup | None:
    logger.debug("Fetching soup for URL: %s", url)
    print(f"Fetching {url}")

    try:
        html_content: str = await fetch(session, url)
        return BeautifulSoup(html_content, "html.parser")
    except ClientResponseError as e:
        print(f"Failed to fetch {url} with status {e.status}")
        logger.error("Failed to fetch %s: %s", url, e)
        return None


async def download_media_items(
    context: CrawlerContext, media_urls: list[str], album_path: Path
) -> list[dict[str, str]]:
    logger.debug("Downloading media items at %s", album_path)

    tasks: list[Any] = [
        download_and_save_media(context.session, url, album_path) for url in media_urls
    ]

    logger.debug("Starting download tasks")
    results: list[dict[str, str]] = await asyncio.gather(*tasks)
    for _ in media_urls:
        context.progress.advance(context.task)

    logger.debug("Download tasks completed")
    return results


# endregion Fetching functions

# region Core album logic


async def process_album(
    context: CrawlerContext,
    album_url: str,
    media_filter: Callable[[BeautifulSoup], list[str]],
    title_extractor: Optional[Callable[[BeautifulSoup], str]] = None,
    title: Optional[str] = None,
    retries: int = 0,
) -> list[dict[str, str]]:
    logger.debug("Processing album for URL: %s", album_url)

    if retries > 5:
        msg: str = f"Max depth reached for {album_url}. Skipping..."
        logger.error(msg)
        print(msg)
        return []

    if album_url.endswith("/"):
        album_url = album_url[:-1]

    soup: BeautifulSoup | None = await fetch_soup(context.session, album_url)
    if soup is None:
        logger.error("Failed to fetch or parse album page: %s", album_url)
        return []

    try:
        # Extract the title if a title_extractor is provided; otherwise, use the given title
        if title_extractor:
            logger.debug("Extracting title from soup")
            title = title_extractor(soup)
        if not title:
            logger.error("Title could not be determined for album: %s", album_url)
            raise ValueError("Title could not be determined")

        media_urls: list[str] = list(set(media_filter(soup)))
        logger.info("Extracted title: %s", title)
        print(f"Title: {title}")
        logger.info("Media URLs: %d", len(media_urls))
        print(f"Media URLs: {len(media_urls)}")
    except (TypeError, ValueError) as e:
        print(f"Failed to process album: {e}. Retrying...")
        logger.exception("Failed to process album %s", album_url)
        return await process_album(
            context, album_url, media_filter, title_extractor, title, retries + 1
        )

    album_path: Path = get_final_path(context.download_path, title)
    logger.info("Saving album to path: %s", album_path)

    return await download_media_items(context, media_urls, album_path)


# endregion Core album logic
