"""Downloader for https://eromexxx.com"""

from __future__ import annotations

import asyncio
from itertools import chain
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from core_helpers.logs import logger
from rich import print
from typing_extensions import override

from ..base_crawler import BaseCrawler

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from urllib.parse import ParseResult

    from bs4 import BeautifulSoup, Tag


class EromeXXXCrawler(BaseCrawler):
    site_url = "https://eromexxx.com"
    headers = {"Referer": site_url, "Origin": site_url}
    models_url: str = site_url + "/models/"
    model_url: str = site_url + "/model/"
    categories_url: str = site_url + "/categories/"
    category_url: str = site_url + "/category/"
    video_url: str = site_url + "/video/"

    def print_help_message(self) -> None:
        print(f"""[bold yellow]Warning:[/] URL not supported. Please provide \
one of the following URLs:
- Model URL: {self.model_url}<model_name>
- All Models URL: {self.models_url}
- Category URL: {self.category_url}<category_name> or {self.site_url}/<category_name>
- All Categories URL: {self.categories_url}
- Single Post URL: {self.site_url}/<post_id>
""")

    def _validate_url(self, url: str) -> str:
        """
        Validate the given URL and extract the path component.

        Args:
            url (str): The URL to validate.

        Returns:
            str: The path component of the URL if valid, otherwise an empty
            string.
        """
        parsed_url: ParseResult = urlparse(url)
        if parsed_url.netloc != urlparse(self.site_url).netloc:
            return ""

        path: list[str] = parsed_url.path.strip("/").split("/")
        if len(path) != 1:
            return ""

        return path[0]

    def is_category_url(self, url: str) -> bool:
        """
        Determine if the given URL is a category URL.

        Args:
            url (str): The URL to check.

        Examples:
            - https://eromexxx.com/category/category-name (True)
            - https://eromexxx.com/categories/ (False)
            - https://eromexxx.com/model/model-name (False)
            - https://eromexxx.com/asian (True)

        Returns:
            bool: True if the URL is a category URL, False otherwise.
        """
        if url.startswith(self.category_url) and (
            url.rstrip("/") != self.category_url.rstrip("/")
        ):
            return True

        path: str = self._validate_url(url)
        if not path:
            return False
        if path in ["models", "model", "categories", "category"]:
            return False

        return "-" not in path and path.isalpha()

    def is_post_url(self, url: str) -> bool:
        """
        Determine if the given URL is a post URL.

        Args:
            url (str): The URL to check.

        Examples:
            - https://eromexxx.com/video/12345-post-title (True)
            - https://eromexxx.com/model/model-name (False)
            - https://eromexxx.com/category/category-name (False)
            - https://eromexxx.com/abbxeh-189 (True)

        Returns:
            bool: True if the URL is a post URL, False otherwise.
        """
        if url.startswith(self.video_url) and url.rstrip("/") != self.video_url.rstrip(
            "/"
        ):
            return True
        return "-" in self._validate_url(url)

    @override
    def get_album_title(self, soup: BeautifulSoup, url: str) -> str:
        return url.rstrip("/").split("/")[-1]

    @override
    async def get_media_urls(self, soup: BeautifulSoup, url: str) -> list[str]:
        """
        Filter and retrieve media URLs from the BeautifulSoup object.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page.

        Returns:
            list[str]: A list of media URLs found on the page.
        """
        videos: list[str] = [
            video_source["src"] for video_source in soup.find_all("source")
        ]
        images: list[str] = [
            image["data-src"]
            for image in soup.find_all("img", class_="img-back lazyload")
        ]
        return images + videos

    async def bulk_download(self, url: str) -> list[dict[str, str]]:
        """
        Download media from all albums of a model or category URL.

        Args:
            url (str): The URL of the model or category to download media from.

        Returns:
            list[dict[str, str]]: A list of dictionaries with information about
            each downloaded media item.
        """
        logger.info(f"Downloading albums from {url}")
        soup: BeautifulSoup = await self.fetch_soup(url)

        try:
            # Get pagination items
            pagination: Tag | None = soup.select_one("ul.pagination")
            # Get the last page number
            last_page = int(pagination.find_all("li")[-2].get_text(strip=True))
        except AttributeError:
            # Only one page, return the current page
            last_page = 1

        tasks = [
            self.get_media_from_page(f"{url}page/{page}/")
            for page in range(1, last_page + 1)
        ]
        media_urls: list[str] = list(chain.from_iterable(await asyncio.gather(*tasks)))

        return await self.process_album(url, media_urls=media_urls)

    async def all_models_download(self) -> list[dict[str, str]]:
        print("[yellow]Downloading all models is not implemented yet.[/]")
        return []

    async def all_categories_download(self) -> list[dict[str, str]]:
        print("[yellow]Downloading all categories is not implemented yet.[/]")
        return []

    async def post_download(self, post_url: str) -> list[dict[str, str]]:
        """
        Download media from a single post URL.

        Args:
            post_url (str): The URL of the post to download media from.

        Returns:
            list[dict[str, str]]: A list of dictionaries with information about
            each downloaded media item.
        """
        return await self.process_album(post_url)

    async def get_media_from_page(self, url: str) -> list[str]:
        """
        Callback to retrieve all media URLs from a specific paginated page of
        albums.

        Args:
            url (str): The URL of the page to retrieve media from.

        Returns:
            list[str]: A list of media URLs found on the specified page.
        """

        async def fetch_and_extract(album: str) -> list[str]:
            """fetch_and_extract === process_album logic"""
            soup: BeautifulSoup = await self.fetch_soup(album)
            return await self.get_media_urls(soup, album)

        soup: BeautifulSoup = await self.fetch_soup(url)

        page_albums: list[str] = [
            album["href"] for album in soup.find_all("a", class_="athumb thumb-link")
        ]
        tasks = [fetch_and_extract(album) for album in page_albums]
        return list(chain.from_iterable(await asyncio.gather(*tasks)))

    @override
    async def download(self, url: str) -> list[dict[str, str]]:
        """
        Download media from the given URL.

        It supports model URLs, category URLs, all models URL,
        all categories URL, and single post URLs. If the URL is not
        supported, it prints a help message.

        Args:
            url (str): The URL of the EromeXXX model to download media from.

        Returns:
            list[dict[str, str]]: A list of dictionaries with information about
            each downloaded media item.
        """
        url = url if url.endswith("/") else url + "/"
        try:
            response = await self.downloader.fetch(url, "HEAD", raw_response=True)
            response.raise_for_status()
            if (
                response.status == 301
                and response.headers.get("Location") == self.site_url
            ):
                self.print_help_message()
                return []
        except Exception as e:
            print(f"Failed to access {url}: {e}")
            return []

        if url == self.models_url:
            return await self.all_models_download()
        if url == self.categories_url:
            return await self.all_categories_download()
        if self.is_post_url(url):
            return await self.post_download(url)
        if any([url.startswith(self.model_url), self.is_category_url(url)]):
            return await self.bulk_download(url)
        else:
            self.print_help_message()
            return []
