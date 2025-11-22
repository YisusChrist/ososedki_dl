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
    from asyncio import Future
    from collections.abc import Callable
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
            f"""[bold yellow]Warning:[/bold yellow] URL not supported. Please \
provide one of the following URLs:
- Model URL: {self.model_url}<model_name>
- All Models URL: {self.models_url}
- Category URL: {self.category_url}<category_name> or {self.site_url}/<category_name>
- All Categories URL: {self.categories_url}
- Single Post URL: {self.site_url}/<post_id>
"""
        )

    def _validate_url(self, url: str) -> str:
        parsed_url: ParseResult = urlparse(url)
        if parsed_url.netloc != urlparse(self.site_url).netloc:
            return ""

        path: list[str] = parsed_url.path.strip("/").split("/")
        if len(path) != 1:
            return ""

        return path[0]

    def is_category_url(self, url: str) -> bool:
        if url.startswith(self.category_url):
            return True

        path: str = self._validate_url(url)
        if not path:
            return False
        if path in ["models", "model", "categories", "category"]:
            return False

        return "-" not in path and path.isalpha()

    def is_post_url(self, url: str) -> bool:
        if url.startswith(self.video_url) and url.rstrip("/") != self.video_url.rstrip(
            "/"
        ):
            return True
        return "-" in self._validate_url(url)

    async def media_filter(self, soup: BeautifulSoup) -> list[str]:
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
        get_media_func: Callable[..., Future[list[str]]],
        **kwargs: str,
    ) -> list[str]:
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

        page_tasks = [
            get_media_func(**kwargs, page=page) for page in range(1, last_page + 1)
        ]
        return list(chain.from_iterable(await gather(*page_tasks)))

    async def bulk_download(self, url: str) -> list[dict[str, str]]:
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
            url, self.media_filter, title=title, media_urls=media_urls
        )

    async def all_models_download(self) -> list[dict[str, str]]:
        raise NotImplementedError

    async def all_categories_download(self) -> list[dict[str, str]]:
        raise NotImplementedError

    async def post_download(self, post_url: str) -> list[dict[str, str]]:
        title: str = post_url.rstrip("/").split("/")[-1]
        return await self.process_album(post_url, self.media_filter, title=title)

    async def get_media_from_page(self, url: str, page: int) -> list[str]:
        page_url: str = f"{url}page/{page}/"
        soup: BeautifulSoup | None = await self.fetch_soup(page_url)
        if not soup:
            return []

        page_albums: list[str] = [
            album["href"]
            for album in soup.find_all("a", class_="athumb thumb-link")
        ]
        tasks = [self.find_media(album) for album in page_albums]
        return list(chain.from_iterable(await gather(*tasks)))

    async def find_media(self, album_url: str) -> list[str]:
        soup: BeautifulSoup | None = await self.fetch_soup(album_url)
        if soup is None:
            return []

        return list(set(await self.media_filter(soup)))

    @override
    async def download(self, url: str) -> list[dict[str, str]]:
        """
        Download all media from a given EromeXXX model URL.

        Fetches the model page, determines the total number of albums,
        retrieves all album URLs across paginated pages, and downloads media
        from each album. Returns a list of dictionaries containing the results
        of each media download. Returns an empty list if the model page or
        required elements are missing, or if no albums are found.

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
