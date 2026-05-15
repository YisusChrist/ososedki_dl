"""Downloader for https://wildskirts.com"""

from __future__ import annotations

import asyncio
from itertools import chain
from typing import TYPE_CHECKING

from typing_extensions import override

from ..base_crawler import BaseCrawler

if TYPE_CHECKING:

    from bs4 import BeautifulSoup
    from bs4.element import NavigableString, Tag


class WildskirtsCrawler(BaseCrawler):
    site_url = "https://wildskirts.com"
    base_photos_url: str = "https://photos.wildskirts.com"
    base_videos_url: str = "https://video.wildskirts.com"
    headers = {"Referer": site_url + "/"}

    def get_total_items(self, soup: BeautifulSoup, item: str) -> int:
        content_div: Tag | NavigableString | None = soup.find(
            "div", class_=f"text-center mx-4 cursor-pointer tab-{item}"
        )
        if not content_div:
            return 0

        p: Tag | NavigableString | None | int = content_div.find("p")
        try:
            return int(p.text)
        except ValueError:
            return 0

    def _extract_from_soup(self, soup: BeautifulSoup) -> list[str]:
        images: list[str] = [
            image["src"]
            for image in soup.find_all("img")
            if self.base_photos_url in image["src"]
            and "preview" not in image["src"]
            and "profile_photo" not in image["src"]
        ]
        videos: list[str] = [
            video["src"]
            for video in soup.find_all("video")
            if self.base_videos_url in video["src"]
            and not video["src"].endswith("#t=0.001")
        ]
        return images + videos

    async def fetch_media_urls(self, url: str) -> list[str]:
        """
        Asynchronously fetches and returns a list of media URLs from the
        specified page URL.

        Args:
            url (str): The URL of the page to extract media URLs from.

        Returns:
            list[str]: A list of media URLs found on the page, or an empty list
            if the page could not be fetched or parsed.
        """
        return self._extract_from_soup(await self.fetch_soup(url))

    @override
    async def get_album_title(): ...

    @override
    async def get_media_urls(self, soup: BeautifulSoup) -> list[str]:
        """
        https://api.wildskirts.com/api/media/<profile_id>
        e.g. https://api.wildskirts.com/api/media/11530
        e.g. https://api.wildskirts.com/api/media/21734

        It returns a JSON with all media items like this:
        {
            "media": {
                "items": {
                    "1": {
                        "p": "preview_url",
                        "t": "photo"/"video",
                        "u": "media_url",
                        "w": width,
                        "h": height,
                        "l": "uri",
                        "o": index,
                        "bg": "background_color",
                        "ts": "upload_timestamp"
                    },
                "count": 169
            },
            "status": "success"
        }

        Extract profile id from:
        <input type="hidden" name="commentable_id" value="<profile_id>" />
        """
        total_pictures: int = self.get_total_items(soup, "photos")
        total_videos: int = self.get_total_items(soup, "videos")
        total_items: int = min(total_pictures + total_videos, 30)

        print(f"Total items: {total_items}")

        urls: list[str] = [f"{self.profile_url}/{i}" for i in range(1, total_items + 1)]
        for url in urls:
            print(f"Constructed URL: {url}")

        # Fetch media URLs concurrently
        tasks = [self.fetch_media_urls(url) for url in urls]
        return list(chain.from_iterable(await asyncio.gather(*tasks)))

    @override
    async def download(self, url: str) -> list[dict[str, str]]:
        """
        Downloads all media items from a Wildskirts profile URL.

        Fetches the profile page, determines the total number of photos and
        videos, constructs URLs for each media item, retrieves all media URLs
        concurrently, and downloads the media to a local album path.

        Args:
            url (str): The Wildskirts profile URL to download media from.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing information
            about each downloaded media item.
        """
        # ! Beware, the trailing slash may return different results
        self.profile_url: str = url.rstrip("/")
        profile: str = self.profile_url.split("/")[-1]
        return await self.process_album(self.profile_url, title=profile)
