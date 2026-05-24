"""Downloader for https://bunkr-albums.io"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from rich import print
from typing_extensions import override

from ..base_crawler import BaseCrawler

if TYPE_CHECKING:
    from pathlib import Path

    from bs4 import BeautifulSoup


class BunkrAlbumsCrawler(BaseCrawler):
    site_url = "https://balbums.st"
    site_aliases = ("https://bunkr-albums.io",)

    @override
    def get_album_title(self, soup: BeautifulSoup, url: str) -> str:
        return url.split("/")[-1]

    @override
    async def get_media_urls(self, soup: BeautifulSoup, url: str) -> list[str]:
        """
        Extracts and resolves all unique Bunkr album URLs from the given page.

        Fetches the HTML content of the specified URL, identifies all anchor
        tags with hrefs starting with "https://bunkr", removes duplicates, and
        resolves each to its final destination URL. Returns an empty list;
        downloading functionality is not yet implemented.

        Args:
            soup (BeautifulSoup): The parsed HTML content of the page.
            url (str): The URL of the page to scan for Bunkr album links (not
                used in the current implementation).

        Returns:
            list[str]: A list of resolved album URLs found on the page.
            Currently returns an empty list as the downloading functionality is
            not implemented.
        """
        # Find all links that start with https://bunkrrr.org/a/
        urls: list[str] = [
            u["href"]
            for u in soup.find_all("a")
            if u["href"].startswith("https://bunkr")
        ]

        urls = list(set(urls))
        # Every url inside the list redirects to a different domain
        # so we need to resolve the real domain
        tasks = [
            self.downloader.fetch(
                u,
                "HEAD",
                response_property="url",
                allow_redirects=True,
            )
            for u in urls
        ]
        real_urls: list[str] = await asyncio.gather(*tasks)

        print(f"Found {len(real_urls)} albums on the page:")
        print(real_urls)

        # TODO: Try to call the cyberdrop_dl program to download the albums

        return []

    async def cyberdrop_dl(
        self, url: str, download_path: Path, real_urls: list[str]
    ) -> None:
        return

        from cyberdrop_dl.managers.manager import Manager
        from cyberdrop_dl.scraper.crawlers.bunkrr_crawler import BunkrrCrawler
        from cyberdrop_dl.utils.dataclasses.url_objects import ScrapeItem

        manager = Manager()
        manager.startup()

        # Initialize the Bunkrr Crawler
        bunkrr_crawler = BunkrrCrawler(manager)

        # Create ScrapeItems and trigger the download process
        for real_url in real_urls:
            scrape_item = ScrapeItem(
                url=real_url,
                parent_title="",  # You can pass the title if you have it or leave it empty
                is_album=True,
            )
            await bunkrr_crawler.fetch(scrape_item)
