"""Downloader for https://fapello.is"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich import print
from typing_extensions import override

from ...utils import get_final_path
from .._common import download_media_items
from ..simple_crawler import SimpleCrawler

if TYPE_CHECKING:
    from pathlib import Path

    from ...download import SessionType
    from .._common import CrawlerContext


class FapelloIsCrawler(SimpleCrawler):
    site_url = "https://fapello.is"
    download_url: str = site_url + "/api/media"

    async def fetch_media_urls(
        self, session: SessionType, url: str, referer_url: str
    ) -> list[dict[str, str]] | str:
        headers: dict[str, str] = {"Referer": referer_url}
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                return []
            return await response.json()

    @override
    async def download(self, url: str) -> list[dict[str, str]]:
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
                self.context.session, fetch_url, url
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

        return await download_media_items(
            session=self.context.session,
            media_urls=urls,
            album_path=album_path,
            progress=self.context.progress,
            task=self.context.task,
        )
