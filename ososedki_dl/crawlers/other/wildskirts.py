"""Downloader for https://wildskirts.com"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from bs4 import NavigableString
from core_helpers.logs import logger
from typing_extensions import override

from ..base_crawler import BaseCrawler

if TYPE_CHECKING:
    from bs4 import BeautifulSoup, Tag


class WildskirtsCrawler(BaseCrawler):
    # ! Beware, the trailing slash may return different results
    site_url = "https://wildskirts.com"
    base_photos_url: str = "https://photos.wildskirts.com"
    base_videos_url: str = "https://video.wildskirts.com"
    api_url: str = "https://api.wildskirts.com/api/media"
    headers = {"Referer": site_url + "/"}
    max_concurrent_downloads = 5
    api = True

    def get_total_items(self, soup: BeautifulSoup, item: str) -> int:
        content_div: Tag | NavigableString | None = soup.find(
            "div", class_=f"text-center mx-4 cursor-pointer tab-{item}"
        )
        if not content_div:
            return 0

        p: Tag | NavigableString | None | int = content_div.find("p")
        try:
            return int(p.text)
        except (ValueError, AttributeError):
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
            for video in soup.find_all("source")
            if self.base_videos_url in video["src"]
            and not video["src"].endswith("#t=0.001")
        ]

        logger.debug(
            f"Extracted {len(images)} image URLs and {len(videos)} video URLs from soup"
        )
        return images + videos

    async def find_media_from_api(self, soup: BeautifulSoup) -> list[str]:
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
        profile_id_input: Tag | NavigableString | None = soup.find(
            "input", {"name": "commentable_id", "type": "hidden"}
        )
        if not profile_id_input or isinstance(profile_id_input, NavigableString):
            logger.error("Could not find profile ID in the page")
            return []

        profile_id: str = profile_id_input["value"]  # type: ignore
        api_url: str = f"{self.api_url}/{profile_id}"
        logger.debug(f"Fetching media URLs from API endpoint: {api_url}")

        data = await self.downloader.fetch(api_url, response_property="json")
        media_items = data.get("media", {}).get("items", {})
        urls = [item.get("u") for item in media_items.values() if item.get("u")]
        logger.debug(f"Extracted {len(urls)} media URLs from API response")

        return urls

    async def find_media_from_soup(self, soup: BeautifulSoup, url: str) -> list[str]:
        """
        Determines the total number of photos and videos, constructs URLs for
        each media item, retrieves all media URLs concurrently and returns the
        complete list of media URLs.

        Args:
            soup (BeautifulSoup): The parsed HTML content of the profile page.
            url (str): The URL of the profile page to fetch media from.

        Returns:
            list[str]: A list of media URLs extracted from the profile page.
        """
        total_pictures: int = self.get_total_items(soup, "photos")
        total_videos: int = self.get_total_items(soup, "videos")
        total_items: int = total_pictures + total_videos
        logger.debug(
            f"Total pictures: {total_pictures}, Total videos: "
            f"{total_videos}, Total items: {total_items}"
        )

        urls: list[str] = [f"{url}/{i}" for i in range(1, total_items + 1)]

        results: list[str] = []
        # Fetch media URLs concurrently
        for url in urls:
            results.extend(self._extract_from_soup(await self.fetch_soup(url)))
            logger.debug(f"Extracted {len(results)} media URLs so far from {url}...")
            if self.downloader.debug:
                print(f"Extracted {len(results)} media URLs so far...")

            await asyncio.sleep(0.5)

        return results

    @override
    def get_album_title(self, soup: BeautifulSoup, url: str) -> str:
        """
        Extracts the album title from the URL by taking the last segment after
        the final slash.

        Args:
            soup (BeautifulSoup): The parsed HTML content of the page (not used
                in this method).
            url (str): The URL of the page being processed.

        Returns:
            str: The extracted album title derived from the URL.
        """
        return url.split("/")[-1]

    @override
    async def get_media_urls(self, soup: BeautifulSoup, url: str) -> list[str]:
        """
        Determines whether to fetch media URLs using the API or by parsing the
        soup, and returns the list of media URLs accordingly.

        Args:
            soup (BeautifulSoup): The parsed HTML content of the page.
            url (str): The URL of the page being processed.

        Returns:
            list[str]: A list of media URLs extracted from the page, either via
            the API or by parsing the soup.
        """
        if self.api:
            return await self.find_media_from_api(soup)
        else:
            return await self.find_media_from_soup(soup, url)
