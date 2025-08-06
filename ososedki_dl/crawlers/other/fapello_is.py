"""Downloader for https://fapello.is"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich import print
from typing_extensions import override

from ...utils import get_final_path
from ..base_crawler import BaseCrawler

if TYPE_CHECKING:
    from pathlib import Path


class FapelloIsCrawler(BaseCrawler):
    site_url = "https://fapello.is"
    download_url: str = site_url + "/api/media"

    async def fetch_media_urls(
        self, url: str, referer_url: str
    ) -> list[dict[str, str]] | str:
        """
        Asynchronously retrieves media metadata from the specified API URL with
        a custom referer header.

        Args:
            url (str): The API endpoint to fetch media data from.
            referer_url (str): The referer URL to include in the request
                headers.

        Returns:
            list[dict[str, str]] | str: A list of media metadata dictionaries
            if the response is successful, or the raw JSON string if the
            response is not a list.
        """
        headers: dict[str, str] = {"Referer": referer_url}
        async with self.context.session.get(url, headers=headers) as response:
            if response.status != 200:
                return []
            return await response.json()

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
        profile_url: str = url
        if profile_url.endswith("/"):
            profile_url = profile_url[:-1]

        profile_id: str = profile_url.split("/")[-1]
        i = 1

        title: str = ""
        urls: list[str] = []
        print(f"Fetching data from profile {profile_id}...")
        while True:
            print(f"Fetching page {i} for profile {profile_id}...")
            fetch_url: str = f"{self.download_url}/{profile_id}/{i}/1"
            album: list[dict[str, str]] | str = await self.fetch_media_urls(
                fetch_url, url
            )
            if not album or album == "null":
                break

            if isinstance(album, str):
                print("Error fetching album:", album)
                break

            if not title:
                title = album[0]["name"]
            urls += [media["newUrl"] for media in album if media["newUrl"]]
            i += 1

        print(f"Found {len(urls)} media items in profile {profile_id}")

        album_path: Path = get_final_path(self.context.download_path, title)

        return await self.download_media_items(urls, album_path)
