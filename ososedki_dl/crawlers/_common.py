"""Common functions for crawlers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiohttp import ClientResponseError
from bs4 import BeautifulSoup
from rich import print

from ..download import download_and_save_media, fetch
from ..utils import get_final_path

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Awaitable, Callable, Optional

    from rich.progress import Progress, TaskID

    from ..download import SessionType


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
    print(f"Fetching {url}")
    try:
        html_content: str = await fetch(session, url)
        return BeautifulSoup(html_content, "html.parser")
    except ClientResponseError as e:
        print(f"Failed to fetch {url} with status {e.status}")
        return None


async def download_media_items(
    session: SessionType,
    media_urls: list[str],
    album_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    tasks: list[Any] = [
        download_and_save_media(session=session, url=url, album_path=album_path)
        for url in media_urls
    ]

    results: list[dict[str, str]] = await asyncio.gather(*tasks)
    for _ in media_urls:
        progress.advance(task)

    return results


# endregion Fetching functions

# region Core album logic


async def process_album(
    context: CrawlerContext,
    album_url: str,
    media_filter: Callable[[BeautifulSoup], Awaitable[list[str]]],
    title_extractor: Optional[Callable[[BeautifulSoup], str]] = None,
    title: Optional[str] = None,
    retries: int = 0,
) -> list[dict[str, str]]:
    """
    Asynchronously processes an album page by extracting media URLs, determining the album title, and downloading all associated media items.
    
    Attempts to fetch and parse the album page, extract the album title (using a provided extractor or fallback), and filter media URLs asynchronously. Retries up to five times on extraction errors. Downloads all found media items to a computed album path and returns a list of download results.
    
    Parameters:
        album_url (str): The URL of the album page to process.
        media_filter (Callable[[BeautifulSoup], Awaitable[list[str]]]): Asynchronous function to extract media URLs from the parsed HTML.
        title_extractor (Optional[Callable[[BeautifulSoup], str]]): Optional function to extract the album title from the parsed HTML.
        title (Optional[str]): Optional fallback title for the album.
    
    Returns:
        list[dict[str, str]]: A list of dictionaries containing the results of each media download. Returns an empty list if the album cannot be processed.
    """
    if retries > 5:
        print(f"Max depth reached for {album_url}. Skipping...")
        return []

    if album_url.endswith("/"):
        album_url = album_url[:-1]

    soup: BeautifulSoup | None = await fetch_soup(context.session, album_url)
    if soup is None:
        return []

    try:
        # Extract the title if a title_extractor is provided; otherwise, use the given title
        if title_extractor:
            title = title_extractor(soup)
        if not title:
            raise ValueError("Title could not be determined")

        media_urls: list[str] = list(set(await media_filter(soup)))
        print(f"Title: {title}")
        print(f"Media URLs: {len(media_urls)}")
    except (TypeError, ValueError) as e:
        print(f"Failed to process album: {e}. Retrying...")
        return await process_album(
            context, album_url, media_filter, title_extractor, title, retries + 1
        )

    album_path: Path = get_final_path(context.download_path, title)

    return await download_media_items(
        context.session,
        media_urls,
        album_path,
        context.progress,
        context.task,
    )


# endregion Core album logic
