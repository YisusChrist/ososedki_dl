"""Base crawler class for handling common crawling tasks."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from aiohttp.client_exceptions import ClientResponseError
from bs4 import BeautifulSoup
from core_helpers.logs import logger
from requests import HTTPError
from rich import print

from ..consts import MAX_RETRIES
from ..download import Downloader
from ..progress import AlbumProgress
from ..utils import get_final_path

if TYPE_CHECKING:
    from argparse import Namespace
    from pathlib import Path

    from rich.progress import TaskID

    from ..download import SessionType


class BaseCrawler(ABC):
    """Abstract base class for crawlers, providing common functionality."""

    site_url: str
    site_aliases: tuple[str, ...] = ()
    session: SessionType
    download_path: Path
    base_image_path: str | None = None
    headers: dict[str, str] | None = None
    max_concurrent_downloads: int = 30

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
        self.downloader = Downloader(
            self.session, self.headers, args.check_cache, debug=args.debug
        )

    @property
    def base_media_url(self) -> str:
        return self.site_url + (self.base_image_path or "")

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """
        Determines if this crawler can handle the given URL by checking the
        primary site_url and any historical domain aliases.

        Args:
            url (str): The URL to check against the crawler's supported domains.

        Returns:
            bool: True if the crawler can handle the URL, False otherwise.
        """
        url_domain = urlparse(url).netloc.lower()
        site_domain = urlparse(cls.site_url).netloc.lower()

        # Check primary domain
        if url_domain == site_domain:
            return True

        # Check historical domains
        for alias in cls.site_aliases:
            if url_domain == urlparse(alias).netloc.lower():
                return True

        return False

    @abstractmethod
    def get_album_title(self, soup: BeautifulSoup, url: str) -> str:
        """
        Extracts and returns the album title from the given URL and parsed HTML.

        Args:
            soup (BeautifulSoup): Parsed HTML content of the album page.
            url (str): The URL of the album page being processed.

        Returns:
            str: The extracted album title.
        """
        raise NotImplementedError(
            "Each crawler must implement its own get_album_title method"
        )

    @abstractmethod
    async def get_media_urls(self, soup: BeautifulSoup, url: str) -> list[str]:
        """
        Asynchronously extracts and returns a list of media URLs from the given
        album URL and parsed HTML.

        Args:
            soup (BeautifulSoup): Parsed HTML content of the album page.
            url (str): The URL of the album page being processed.

        Returns:
            list[str]: A list of media URLs extracted from the album page.
        """
        raise NotImplementedError(
            "Each crawler must implement its own get_media_urls method"
        )

    async def download(self, url: str) -> list[dict[str, str]]:
        """
        Asynchronously downloads and parses content from the specified URL.

        This method serves as the main entry point for processing a given URL.
        It calls the `process_album` method, which handles the core logic of
        fetching the album page, extracting the title and media URLs, and
        downloading the media items.

        Subclasses can override this method if they need to implement custom
        behavior for different types of URLs (e.g., model pages vs. album
        pages), but by default it will simply delegate to `process_album`.

        Args:
            url (str): The URL to crawl and extract data from.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing extracted
            data.

        Raises:
            NotImplementedError: If the method is not implemented by a
                subclass.
        """
        return await self.process_album(url)

    # region Fetching functions

    async def fetch_soup(self, url: str) -> BeautifulSoup:
        """
        Fetches HTML and returns a BeautifulSoup object.

        Args:
            url (str): The URL to fetch and parse.

        Returns:
            BeautifulSoup: Parsed HTML content of the page.

        Raises:
            ValueError: If the fetched HTML content is empty or cannot be parsed.
        """
        logger.debug(f"Fetching soup for URL: {url}")
        # print(f"Fetching {url}")

        html_content: str = await self.downloader.fetch(url)
        if not html_content:
            logger.error(f"Failed to fetch {url}: empty HTML content")
            raise ValueError(f"Empty HTML content received from {url}")

        return BeautifulSoup(html_content, "html.parser")

    async def download_media_items(
        self,
        media_urls: list[str],
        album_title: str,
        album_path: Path,
    ) -> list[dict[str, str]]:
        logger.debug(
            f"Downloading {len(media_urls)} media items for album '{album_title}'"
        )

        # 1. Create a semaphore to limit concurrent network requests
        semaphore = asyncio.Semaphore(self.max_concurrent_downloads)

        # 2. Create a worker wrapper that respects the semaphore
        async def sem_worker(url: str) -> dict[str, str]:
            async with semaphore:
                return await self.downloader.download_and_save_media(url, album_path)

        # 3. Create the tasks using the wrapper instead of calling the method directly
        tasks = [sem_worker(url) for url in media_urls]

        results: list[dict[str, str]] = []
        with AlbumProgress() as progress:
            task: TaskID = progress.add_task(
                f"Downloading {album_title}...", total=len(media_urls)
            )
            for future in asyncio.as_completed(tasks):
                result: dict[str, str] = await future
                results.append(result)
                progress.advance(task)
                logger.info(f"Downloaded: {result['url']} - Status: {result['status']}")

        return results

    # endregion Fetching functions

    # region Core album logic

    async def process_album(
        self,
        album_url: str,
        title: str | None = None,
        media_urls: list[str] | None = None,
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
            title (str, optional): Fallback title for the album.
            media_urls (list[str], optional): Pre-extracted list of media
                URLs to download. If not provided, media URLs will be extracted
                from the album page.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing the results of
            each media download or an empty list otherwise.
        """
        logger.debug(f"Processing album: {album_url}")

        album_url = album_url.rstrip("/")
        retries = 0

        while retries <= MAX_RETRIES:
            if retries > 0:
                logger.info(
                    f"Retrying ({retries}/{MAX_RETRIES}) for album: {album_url}"
                )
                print(f"Retrying ({retries}/{MAX_RETRIES}) for album: {album_url}")
            try:
                soup = await self.fetch_soup(album_url)

                # Extract the title if a title_extractor is provided; otherwise, use the given title
                if not title:
                    title = self.get_album_title(soup, album_url)
                if not title:
                    raise ValueError("Title could not be determined")

                media_urls = media_urls or await self.get_media_urls(soup, album_url)
                media_urls = list(set(media_urls))
                # print(f"Title: {title}")
                # print(f"Media URLs: {len(media_urls)}")
            except (TypeError, ValueError, ClientResponseError, HTTPError) as e:
                logger.exception(f"Error processing album {album_url}")
                print(f"Failed to process album: {e}")
                retries += 1
                continue

            album_path: Path = get_final_path(self.download_path, title)
            return await self.download_media_items(media_urls, title, album_path)

        logger.error(f"Max retries reached for {album_url}. Skipping...")
        print(f"ERROR: Max retries reached for {album_url}. Skipping...")
        return []

    # endregion Core album logic
