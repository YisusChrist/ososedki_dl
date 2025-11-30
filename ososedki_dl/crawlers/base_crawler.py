"""Base crawler class for handling common crawling tasks."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from aiohttp import ClientResponseError
from bs4 import BeautifulSoup
from core_helpers.logs import logger
from rich import print

from ..download import download_and_save_media, fetch
from ..progress import AlbumProgress
from ..utils import get_final_path

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Awaitable, Callable
    from pathlib import Path
    from typing import Any

    from rich.progress import TaskID

    from ..download import SessionType


class BaseCrawler(ABC):
    """Abstract base class for crawlers, providing common functionality."""

    site_url: str
    base_image_path: str | None = None
    session: SessionType
    download_path: Path
    check_cache: bool = False
    headers: dict[str, str] | None = None

    def __init__(self, session: SessionType, args: Namespace) -> None:
        """
        Initialize the BaseCrawler with a given crawling context.

        Args:
            session (SessionType): The HTTP session to use for requests.
            args (Namespace): The command-line arguments containing context such as
                download path and cache checking.
        """
        logger.debug(
            f"Initialized {self.__class__.__name__} with site URL: {self.site_url}"
        )
        self.session = session
        self.download_path = args.dest_path
        self.check_cache = args.check_cache

    @property
    def base_media_url(self) -> str:
        return self.site_url + (self.base_image_path or "")

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
            html_content: str = await fetch(self.session, url)
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
            download_and_save_media(
                self.session, url, album_path, self.check_cache, self.headers
            )
            for url in media_urls
        ]

        results: list[dict[str, str]] = []
        with AlbumProgress() as progress:
            task: TaskID = progress.add_task(
                f"Downloading {album_title}...", total=len(media_urls)
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
        media_urls: list[str] | None = None,
        soup: BeautifulSoup | None = None,
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
            title_extractor (Callable[[BeautifulSoup], str], optional): Function
                to extract the album title from the parsed HTML.
            title (str, optional): Fallback title for the album.
            retries (int): Current retry count for extraction attempts.
            media_urls (list[str], optional): Pre-extracted list of media
                URLs to download.
            soup (BeautifulSoup, optional): Pre-fetched parsed HTML of the album
                page.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing the results of
            each media download or an empty list otherwise.
        """
        if retries > 5:
            print(f"Max depth reached for {album_url}. Skipping...")
            return []

        album_url.rstrip("/")

        soup = soup or await self.fetch_soup(album_url)
        if not soup:
            logger.error(f"Failed to fetch or parse page: {album_url}")
            return []

        try:
            # Extract the title if a title_extractor is provided; otherwise, use the given title
            if title_extractor:
                title = title_extractor(soup)
            if not title:
                raise ValueError("Title could not be determined")

            media_urls = media_urls or list(set(await media_filter(soup)))
            # print(f"Title: {title}")
            # print(f"Media URLs: {len(media_urls)}")
        except (TypeError, ValueError) as e:
            print(f"Failed to process album: {e}. Retrying...")
            return await self.process_album(
                album_url,
                media_filter,
                title_extractor,
                title,
                retries + 1,
                media_urls,
            )

        album_path: Path = get_final_path(self.download_path, title)
        return await self.download_media_items(media_urls, title, album_path)

    # endregion Core album logic
