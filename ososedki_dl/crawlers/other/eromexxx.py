"""Downloader for https://eromexxx.com"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tldextract
from rich import print
from typing_extensions import override

from ...download import download_and_save_media
from ...utils import get_final_path
from .._common import fetch_soup
from ..simple_crawler import SimpleCrawler

if TYPE_CHECKING:
    from pathlib import Path

    from bs4 import BeautifulSoup
    from bs4.element import NavigableString, Tag

    from ...download import SessionType
    from .._common import CrawlerContext


class EromeXXXCrawler(SimpleCrawler):
    site_url = "https://eromexxx.com"

    @override
    async def download(self, url: str) -> list[dict[str, str]]:
        profile_url: str = url
        if profile_url.endswith("/"):
            profile_url = profile_url[:-1]

        profile: str = profile_url.split("/")[-1]

        soup: BeautifulSoup | None = await fetch_soup(self.context.session, profile_url)
        if not soup:
            return []

        # Get the total number of albums
        header: Tag | NavigableString | None = soup.find("div", class_="header-title")
        if not header:
            return []
        span: Tag | NavigableString | None | int = header.find("span")
        if not span or isinstance(span, int):
            return []
        total_albums = int(span.text.strip())
        print(f"Total_albums: {total_albums}")

        # Get all album URLs from pagination
        albums: list[str] = await self.find_albums_with_pagination(
            self.context.session, soup, profile_url, profile
        )
        if not albums:
            print("No albums found.")
            return []

        # Determine the highest album offset
        highest_offset: int = max(
            int(album.split("-")[-1].split("/")[0]) for album in albums
        )
        print(f"Highest_offset: {highest_offset}")
        base_url: str = "".join(profile_url.split("/model"))

        results: list[dict[str, str]] = []
        for i in range(1, highest_offset + 1):
            results += await self.download_album(f"{base_url}-{i}", profile)

        return results

    async def find_albums_with_pagination(
        self, session: SessionType, soup: BeautifulSoup, profile_url: str, profile: str
    ) -> list[str]:
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

        albums: list[str] = []
        for page in range(1, last_page + 1):
            page_url: str = f"{profile_url}/page/{page}"
            page_soup: BeautifulSoup | None = await fetch_soup(session, page_url)
            if not page_soup:
                break
            page_albums: list[str] = self.find_albums_in_soup(page_soup, profile)
            albums.extend(page_albums)

        albums = list(set(albums))  # Remove duplicates
        return albums

    def find_albums_in_soup(self, soup: BeautifulSoup, profile: str) -> list[str]:
        albums: list[str] = []
        for album in soup.find_all("a", class_="athumb thumb-link"):
            if profile in album["href"]:
                albums.append(album["href"])
        return albums

    async def download_album(self, album_url: str, title: str) -> list[dict[str, str]]:
        try:
            soup: BeautifulSoup | None = await fetch_soup(
                self.context.session, album_url
            )
        except ValueError:
            return []

        if not soup:
            return []

        videos: list[str] = [
            video_source["src"] for video_source in soup.find_all("source")
        ]
        images: list[str] = [
            image["data-src"]
            for image in soup.find_all("img", class_="img-back lazyload")
        ]
        urls: list[str] = list(set(images + videos))

        album_path: Path = get_final_path(self.context.download_path, title)

        results: list[dict[str, str]] = []
        for url in urls:
            result: dict[str, str] = await self.download_media(
                self.context.session, url, album_path, album_url
            )
            results.append(result)
            self.context.progress.advance(self.context.task)

        return results

    async def download_media(
        self, session: SessionType, url: str, download_path: Path, album: str = ""
    ) -> dict[str, str]:
        hostname: str = tldextract.extract(url).fqdn

        headers: dict[str, str] = {
            "Referer": album or f"https://{hostname}",
            "Origin": f"https://{hostname}",
            "User-Agent": "Mozilla/5.0",
        }

        return await download_and_save_media(
            session,
            url,
            download_path,
            headers,
        )
