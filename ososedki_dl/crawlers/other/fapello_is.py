"""Downloader for https://fapello.is"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich import print
from typing_extensions import override

from ...consts import DEFAULT_ALBUM_TITLE
from ..base_crawler import BaseCrawler

if TYPE_CHECKING:
    from bs4 import BeautifulSoup


class FapelloIsCrawler(BaseCrawler):
    site_url = "https://fapello.is"
    api_url: str = site_url + "/api/media"
    headers = {"Referer": site_url}

    @override
    def get_album_title(self, soup: BeautifulSoup) -> str:
        title_element = soup.find("h1", class_="text-xl font-semibold text-lead")
        return title_element.text.strip() if title_element else DEFAULT_ALBUM_TITLE

    @override
    async def get_media_urls(self, soup: BeautifulSoup) -> list[str]:
        profile_id: str = self.profile_url.split("/")[-1]
        headers: dict[str, str] = {"Referer": self.profile_url}
        urls: list[str] = []
        page = 1

        print(f"Fetching data from profile {profile_id}...")
        while True:
            print(f"Fetching page {page} for profile {profile_id}...")
            fetch_url: str = f"{self.api_url}/{profile_id}/{page}/1"

            data = await self.downloader.fetch(
                fetch_url, headers=headers, response_property="json"
            )
            if not data or data == "null":
                break

            if isinstance(data, str):
                print("Error fetching data:", data)
                break

            urls.extend([m["newUrl"] for m in data if m["newUrl"]])
            print(f"Found {len(urls)} media URLs so far...")
            page += 1

        return urls

    @override
    async def download(self, url: str) -> list[dict[str, str]]:
        """
        Asynchronously downloads all media items from a given Fapello profile
        URL.

        Iterates through paginated API endpoints to collect media URLs,
        determines the album title, and downloads all found media items to the
        resolved album path.

        Args:
            url (str): The Fapello profile URL to download media from.

        Returns:
            list[dict[str, str]]: A list of dictionaries representing the
            downloaded media items.
        """
        self.profile_url: str = url.rstrip("/")
        return await self.process_album(album_url=self.profile_url)
