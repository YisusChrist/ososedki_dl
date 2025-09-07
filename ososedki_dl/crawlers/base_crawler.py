"""Base crawler class for handling common crawling tasks."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiohttp import ClientResponseError
from bs4 import BeautifulSoup
from rich import print

from ..download import download_and_save_media, fetch
from ..logs import logger
from ..progress import AlbumProgress
from ..utils import get_final_path

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path
    from typing import Any

    from rich.progress import TaskID

    from ..download import SessionType

# region Context class


@dataclass
class CrawlerContext:
    session: SessionType
    download_path: Path
    progress: Optional[Progress] = None
    task: Optional[TaskID] = None


# endregion Context class


class BaseCrawler(ABC):
    """Abstract base class for crawlers, providing common functionality."""

    site_url: str
    context: CrawlerContext

    def __init__(self, context: CrawlerContext) -> None:
        """
        Initialize the BaseCrawler with a given crawling context.

        Args:
            context (CrawlerContext): The context containing configuration and
                state for the crawler instance.
        """
        logger.debug(
            f"Initialized {self.__class__.__name__} with site URL: {self.site_url}"
        )
        self.context = context

    @abstractmethod
    async def download(self, url: str) -> list[dict[str, str]]:
        """
        Asynchronously downloads and parses content from the specified URL.

        Args:
            url (str): The URL to crawl and extract data from.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing extracted
            data.

        Raises:
            NotImplementedError: If the method is not implemented by a
                subclass.
        """
        raise NotImplementedError("Each crawler must implement its own download method")

    # region Fetching functions

    async def fetch_soup(self, url: str) -> BeautifulSoup | None:
        print(f"Fetching {url}")
        try:
            html_content: str = await fetch(self.context.session, url)
            return BeautifulSoup(html_content, "html.parser")
        except ClientResponseError as e:
            print(f"Failed to fetch {url} with status {e.status}")
            return None

    async def download_media_items(
        self,
        media_urls: list[str],
        album_title: str,
        album_path: Path,
    ) -> list[dict[str, str]]:
        tasks: list[Any] = [
            download_and_save_media(self.context.session, url, album_path)
            for url in media_urls
        ]

        results: list[dict[str, str]] = []
        with AlbumProgress() as progress:
            task: TaskID = progress.add_task(
                f"[cyan]Downloading {album_title}...", total=len(media_urls)
            )
            for future in asyncio.as_completed(tasks):
                result: dict[str, str] = await future
                results.append(result)
                progress.advance(task)

        return results

    # endregion Fetching functions

    # region Core album logic

    async def process_album(
        self,
        album_url: str,
        media_filter: Callable[[BeautifulSoup], Awaitable[list[str]]],
        title_extractor: Callable[[BeautifulSoup], str] | None = None,
        title: str | None = None,
        retries: int = 0,
    ) -> list[dict[str, str]]:
        """
        Asynchronously processes an album page by extracting media URLs,
        determining the album title, and downloading all associated media items.

        Attempts to fetch and parse the album page, extract the album title (using
        a provided extractor or fallback), and filter media URLs asynchronously.
        Retries up to five times on extraction errors. Downloads all found media
        items to a computed album path and returns a list of download results.

        Args:
            album_url (str): The URL of the album page to process.
            media_filter (Callable[[BeautifulSoup], Awaitable[list[str]]]):
                Asynchronous function to extract media URLs from the parsed HTML.
            title_extractor (Optional[Callable[[BeautifulSoup], str]]): Optional
                function to extract the album title from the parsed HTML.
            title (Optional[str]): Optional fallback title for the album.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing the results of
            each media download or an empty list otherwise.
        """
        if retries > 5:
            print(f"Max depth reached for {album_url}. Skipping...")
            return []

        if album_url.endswith("/"):
            album_url = album_url[:-1]

        soup: BeautifulSoup | None = await self.fetch_soup(album_url)
        if soup is None:
            return []

        try:
            # Extract the title if a title_extractor is provided; otherwise, use the given title
            if title_extractor:
                title = title_extractor(soup)
            if not title:
                raise ValueError("Title could not be determined")

            media_urls: list[str] = list(set(await media_filter(soup)))
            # print(f"Title: {title}")
            # print(f"Media URLs: {len(media_urls)}")
        except (TypeError, ValueError) as e:
            print(f"Failed to process album: {e}. Retrying...")
            return await self.process_album(
                album_url, media_filter, title_extractor, title, retries + 1
            )

        album_path: Path = get_final_path(self.context.download_path, title)
        return await self.download_media_items(media_urls, title, album_path)

    # endregion Core album logic
