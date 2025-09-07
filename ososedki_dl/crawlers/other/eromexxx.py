"""Downloader for https://eromexxx.com"""

from __future__ import annotations

import asyncio
from itertools import chain
from typing import TYPE_CHECKING

from bs4 import NavigableString
from rich import print
from typing_extensions import override

from ..base_crawler import BaseCrawler

if TYPE_CHECKING:
    from bs4 import BeautifulSoup
    from bs4.element import Tag


class EromeXXXCrawler(BaseCrawler):
    site_url = "https://eromexxx.com"
    headers = {"Referer": site_url, "Origin": site_url}

    async def media_filter(self, soup: BeautifulSoup) -> list[str]:
        videos: list[str] = [
            video_source["src"] for video_source in soup.find_all("source")
        ]
        images: list[str] = [
            image["data-src"]
            for image in soup.find_all("img", class_="img-back lazyload")
        ]
        return images + videos

    @override
    async def download(self, url: str) -> list[dict[str, str]]:
        """
        Download all media from a given EromeXXX profile URL.

        Fetches the profile page, determines the total number of albums,
        retrieves all album URLs across paginated pages, and downloads media
        from each album. Returns a list of dictionaries containing the results
        of each media download. Returns an empty list if the profile page or
        required elements are missing, or if no albums are found.

        Args:
            url (str): The URL of the EromeXXX profile to download media from.

        Returns:
            list[dict[str, str]]: A list of dictionaries with information about
            each downloaded media item.
        """
        profile_url: str = url.rstrip("/")  # normalize URL
        profile: str = profile_url.split("/")[-1]

        soup: BeautifulSoup | None = await self.fetch_soup(profile_url)
        if not soup:
            return []

        # Get the total number of albums
        header: Tag | NavigableString | None = soup.find("div", class_="header-title")
        if not header:
            return []
        span: Tag | NavigableString | None | int = header.find("span")
        if not span or isinstance(span, int):
            return []
        total_albums = int(span.get_text(strip=True))
        print(f"Total_albums: {total_albums}")

        # Get pagination items
        pagination: Tag | NavigableString | None = soup.find("ul", class_="pagination")
        if not pagination or isinstance(pagination, NavigableString):
            return []

        # Get the last page number
        try:
            last_page = int(pagination.find_all("li")[-2].text)
        except AttributeError:
            # Only one page, return the current page
            last_page = 1

        page_tasks = [
            self._get_media_from_page(profile_url, profile, page)
            for page in range(1, last_page + 1)
        ]
        media_urls: list[str] = list(
            chain.from_iterable(await asyncio.gather(*page_tasks))
        )

        if not media_urls:
            print(f"No media found for profile {profile}")
            return []

        return await self.process_album(
            profile_url, self.media_filter, title=profile, media_urls=media_urls
        )

    async def _get_media_from_page(
        self, profile_url: str, profile: str, page: int
    ) -> list[str]:
        page_url: str = f"{profile_url}/page/{page}"
        soup: BeautifulSoup | None = await self.fetch_soup(page_url)
        if not soup:
            return []

        page_albums: list[str] = [
            album["href"]
            for album in soup.find_all("a", class_="athumb thumb-link")
            if profile in album.get("href", "")
        ]
        tasks = [self.find_media(album) for album in page_albums]
        return list(chain.from_iterable(await asyncio.gather(*tasks)))

    async def find_media(self, album_url: str) -> list[str]:
        soup: BeautifulSoup | None = await self.fetch_soup(album_url)
        if soup is None:
            return []

        return list(set(await self.media_filter(soup)))
