"""Downloader for https://wildskirts.com"""

import asyncio
from pathlib import Path
from typing import override

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from ...utils import get_final_path
from .._common import CrawlerContext, download_media_items, fetch_soup
from ..simple_crawler import SimpleCrawler


class WildskirtsCrawler(SimpleCrawler):
    site_url = "https://wildskirts.com"
    base_photos_url: str = "https://photos.wildskirts.com"
    base_videos_url: str = "https://video.wildskirts.com"

    def get_total_items(self, soup: BeautifulSoup, item: str) -> int:
        content_div: Tag | NavigableString | None = soup.find(
            "div", class_=f"text-center mx-4 cursor-pointer tab-{item}"
        )
        if not content_div:
            return 0

        paragraph: Tag | NavigableString | None | int = content_div.find("p")
        if not paragraph:
            return 0
        if isinstance(paragraph, int):
            return paragraph

        return int(paragraph.text)

    def wildskirts_media_filter(self, soup: BeautifulSoup) -> list[str]:
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

    async def fetch_media_urls(self, session: ClientSession, url: str) -> list[str]:
        soup: BeautifulSoup | None = await fetch_soup(session, url)
        return self.wildskirts_media_filter(soup) if soup else []

    @override
    async def download(self, context: CrawlerContext, url: str) -> list[dict[str, str]]:
        profile_url: str = url
        # ! Beware, the trailing slash may return different results
        if profile_url.endswith("/"):
            profile_url = profile_url[:-1]

        profile: str = profile_url.split("/")[-1]

        soup: BeautifulSoup | None = await fetch_soup(context.session, profile_url)
        if not soup:
            return []

        total_pictures: int = self.get_total_items(soup, "photos")
        total_videos: int = self.get_total_items(soup, "videos")
        total_items: int = total_pictures + total_videos

        print(f"Total items: {total_items}")

        urls: list[str] = [f"{profile_url}/{i}" for i in range(1, total_items + 1)]
        # Fetch media URLs concurrently
        media_urls_lists: list[list[str]] = await asyncio.gather(
            *[self.fetch_media_urls(context.session, url) for url in urls]
        )
        # Flatten the list of lists into a single list
        media_urls: list[str] = [url for sublist in media_urls_lists for url in sublist]

        print("Retrieved media URLs")

        album_path: Path = get_final_path(context.download_path, profile)

        return await download_media_items(
            context.session, media_urls, album_path, context.progress, context.task
        )
