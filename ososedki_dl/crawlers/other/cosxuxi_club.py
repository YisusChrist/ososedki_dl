"""Downloader for https://cosxuxi.club"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from ...utils import get_final_path
from .._common import download_media_items, fetch_soup
from ..simple_crawler import SimpleCrawler

if TYPE_CHECKING:
    from pathlib import Path

    from bs4 import BeautifulSoup
    from bs4.element import NavigableString, Tag

    from .._common import CrawlerContext


class CosxuxiClubCrawler(SimpleCrawler):
    site_url = "https://cosxuxi.club"
    base_url: str = ".wp.com/img.nungvl.net/"

    def cosxuxi_club_title_extractor(self, soup: BeautifulSoup) -> str:
        text_div: Tag | NavigableString | None = soup.find("title")
        if not text_div:
            return "Unknown"
        text: str = text_div.text.strip()
        title: str = "Unknown"
        try:
            if "CosXuxi Club: " in text and " - " in text:
                title = text.split("CosXuxi Club: ")[1].split(" - ")[0].strip()
        except IndexError:
            print(f"ERROR: Could not extract title from '{text}'")
        return title

    def cosxuxi_club_media_filter(self, soup: BeautifulSoup) -> list[str]:
        # Find all the images inside the div with the class 'contentme'
        content_div: Tag | NavigableString | None = soup.find("div", class_="contentme")
        if not content_div or isinstance(content_div, NavigableString):
            return []

        return [
            img.get("src")
            for img in content_div.find_all("img")
            if self.base_url in img.get("src")
        ]

    @override
    async def download(self, url: str) -> list[dict[str, str]]:
        album_url: str = url
        if album_url.endswith("/"):
            album_url = album_url[:-1]

        title: str = ""
        urls: list[str] = []

        while True:
            soup: BeautifulSoup | None = await fetch_soup(self.context.session, album_url)
            if not soup:
                break
            page_urls: list[str] = self.cosxuxi_club_media_filter(soup) if soup else []
            if not page_urls:
                break

            urls.extend(page_urls)

            if not title:
                title = self.cosxuxi_club_title_extractor(soup)

            # Check if there is a next page
            next_page: Tag | NavigableString | None = soup.find(
                "a", class_="page-numbers", string="Next >"
            )
            if isinstance(next_page, NavigableString):
                next_page = None
            if not next_page or not next_page.get("href"):
                break
            next_page_url: str | list[str] = next_page.get("href", "")
            if isinstance(next_page_url, list):
                next_page_url = next_page_url[0]
            album_url = self.site_url + next_page_url

        album_path: Path = get_final_path(self.context.download_path, title)

        return await download_media_items(
            self.context.session, urls, album_path, self.context.progress, self.context.task
        )
