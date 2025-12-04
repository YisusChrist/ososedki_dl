"""Downloader for https://eromexxx.com"""

from __future__ import annotations

from asyncio import gather
from itertools import chain
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from bs4 import NavigableString
from rich import print
from typing_extensions import override

from ..base_crawler import BaseCrawler

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from urllib.parse import ParseResult

    from bs4 import BeautifulSoup
    from bs4.element import Tag


class EromeXXXCrawler(BaseCrawler):
    site_url = "https://eromexxx.com"
    headers = {"Referer": site_url, "Origin": site_url}
    models_url: str = site_url + "/models/"
    model_url: str = site_url + "/model/"
    categories_url: str = site_url + "/categories/"
    category_url: str = site_url + "/category/"
    video_url: str = site_url + "/video/"

    def print_help_message(self) -> None:
        print(
            f"""[bold yellow]Warning:[/] URL not supported. Please provide \
one of the following URLs:
- Model URL: {self.model_url}<model_name>
- All Models URL: {self.models_url}
- Category URL: {self.category_url}<category_name> or {self.site_url}/<category_name>
- All Categories URL: {self.categories_url}
- Single Post URL: {self.site_url}/<post_id>
"""
        )

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
        if url.startswith(self.category_url) and url.rstrip(
            "/"
        ) != self.category_url.rstrip("/"):
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
    async def get_media_urls(self, soup: BeautifulSoup) -> list[str]:
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

    async def get_paginated_media(
        self,
        soup: BeautifulSoup,
        get_media_func: Callable[..., Awaitable[list[str]]],
        url: str,
    ) -> list[str]:
        """
        Retrieve all media URLs across paginated pages.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the initial page.
            get_media_func (Callable[..., Awaitable[list[str]]]): The function to
                retrieve media URLs from a specific page.
            url (str): The base URL for pagination.

        Returns:
            list[str]: A list of all media URLs found across paginated pages.
        """
        try:
            # Get pagination items
            pagination: Tag | NavigableString | None = soup.find(
                "ul", class_="pagination"
            )
            # Get the last page number
            last_page = int(pagination.find_all("li")[-2].get_text(strip=True))
        except AttributeError:
            # Only one page, return the current page
            last_page = 1

        tasks = [
            get_media_func(f"{url}page/{page}/") for page in range(1, last_page + 1)
        ]
        return list(chain.from_iterable(await gather(*tasks)))

    async def bulk_download(self, url: str) -> list[dict[str, str]]:
        """
        Download media from all albums of a model or category URL.

        Args:
            url (str): The URL of the model or category to download media from.

        Returns:
            list[dict[str, str]]: A list of dictionaries with information about
            each downloaded media item.
        """
        title: str = url.rstrip("/").split("/")[-1]

        soup: BeautifulSoup | None = await self.fetch_soup(url)
        if not soup:
            return []

        media_urls: list[str] = await self.get_paginated_media(
            soup, self.get_media_from_page, url=url
        )
        if not media_urls:
            print(f"No media found for {title}")
            return []

        return await self.process_album(
            url, title=title, media_urls=media_urls, soup=soup
        )

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
        title: str = post_url.rstrip("/").split("/")[-1]
        return await self.process_album(post_url, title=title)

    async def get_media_from_page(self, url: str) -> list[str]:
        """
        Callback to retrieve all media URLs from a specific paginated page of
        albums.

        Args:
            url (str): The URL of the page to retrieve media from.

        Returns:
            list[str]: A list of media URLs found on the specified page.
        """
        soup: BeautifulSoup | None = await self.fetch_soup(url)
        if not soup:
            return []

        page_albums: list[str] = [
            album["href"] for album in soup.find_all("a", class_="athumb thumb-link")
        ]
        tasks = [self.find_media(album) for album in page_albums]
        return list(chain.from_iterable(await gather(*tasks)))

    async def find_media(self, url: str) -> list[str]:
        """
        Find and return all media URLs from a given URL.

        Args:
            url (str): The URL to retrieve media from.

        Returns:
            list[str]: A list of media URLs found in the album.
        """
        soup: BeautifulSoup | None = await self.fetch_soup(url)
        if not soup:
            return []

        return list(set(await self.get_media_urls(soup)))

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
            response = await self.session.head(url)
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
