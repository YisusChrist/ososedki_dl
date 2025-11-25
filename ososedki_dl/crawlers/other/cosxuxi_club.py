"""Downloader for https://cosxuxi.club"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bs4 import NavigableString
from typing_extensions import override

from ...utils import get_final_path
from ..base_crawler import BaseCrawler

if TYPE_CHECKING:
    from pathlib import Path

    from bs4 import BeautifulSoup, Tag


class CosxuxiClubCrawler(BaseCrawler):
    site_url = "https://cosxuxi.club"
    site_name: str = "CosXuxi Club"
    title_separator: str = " - "

    def cosxuxi_club_title_extractor(self, soup: BeautifulSoup) -> str:
        text_div: Tag | NavigableString | None = soup.find("title")
        if not text_div:
            return "Unknown"
        text: str = text_div.text.strip()
        title: str = "Unknown"

        if f"{self.site_name}: " in text and self.title_separator in text:
            try:
                title = (
                    text.split(f"{self.site_name}: ")[1]
                    .split(self.title_separator)[0]
                    .strip()
                )
            except IndexError:
                print(f"ERROR: Could not extract title from '{text}'")

        return title

    def cosxuxi_club_media_filter(self, soup: BeautifulSoup) -> list[str]:
        """
        Extracts and returns a list of image URLs from the 'contentme' div that
        contain the specified base URL fragment.

        Args:
            soup (BeautifulSoup): Parsed HTML content of the page.

        Returns:
            list[str]: List of image source URLs matching the base URL filter,
            or an empty list if no valid images are found.
        """
        # Find all the images inside the div with the class 'contentme'
        content_div: Tag | NavigableString | None = soup.find("div", class_="contentme")
        if not content_div or isinstance(content_div, NavigableString):
            return []

        return [img.get("src") for img in content_div.find_all("img")]

    @override
    async def download(self, url: str) -> list[dict[str, str]]:
        """
        Asynchronously downloads all media items from a CosXuxi Club album,
        following pagination if present.

        Args:
            url (str): The URL of the CosXuxi Club album to download.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing information
            about each downloaded media item.
        """
        album_url: str = url.rstrip("/")
        title: str = ""
        urls: list[str] = []

        while True:
            soup: BeautifulSoup | None = await self.fetch_soup(album_url)
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

        album_path: Path = get_final_path(self.download_path, title)

        return await self.download_media_items(urls, title, album_path)
