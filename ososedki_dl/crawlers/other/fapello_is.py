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
    def get_album_title(self, soup: BeautifulSoup, url: str) -> str:
        """
        Extracts the album title from the page's HTML soup.

        Args:
            soup (BeautifulSoup): The parsed HTML content of the page.
            url (str): The URL of the page being processed (not used in this
                method).

        Returns:
            str: The extracted album title, or a default title if not found.
        """
        title_element = soup.find("h1", class_="text-xl font-semibold text-lead")
        return title_element.text.strip() if title_element else DEFAULT_ALBUM_TITLE

    @override
    async def get_media_urls(self, soup: BeautifulSoup, url: str) -> list[str]:
        """
        Extracts media URLs from the profile page by paginating through the API.

        Uses the profile ID from the URL to fetch media URLs in batches until no
        more media is found. Returns a list of media URLs or an empty list if
        none are found.

        Args:
            soup (BeautifulSoup): The parsed HTML content of the profile page
                (not used in this method).
            url (str): The profile URL to download media from.

        Returns:
            list[str]: A list of media URLs extracted from the profile, or an
            empty list if no media is found.
        """
        profile_id: str = url.split("/")[-1]
        headers: dict[str, str] = {"Referer": url}
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
