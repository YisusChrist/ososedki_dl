"""Downloader for https://bunkr-albums.io"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich import print
from typing_extensions import override

from ...consts import MAX_TIMEOUT
from ..base_crawler import BaseCrawler

if TYPE_CHECKING:
    from pathlib import Path

    from bs4 import BeautifulSoup


class BunkrAlbumsCrawler(BaseCrawler):
    site_url = "https://bunkr-albums.io"

    async def get_real_url(self, url: str) -> str:
        """
        Resolve and return the final destination URL after following any
        redirects.

        Args:
            url (str): The initial URL to resolve.

        Returns:
            str: The fully resolved URL after all redirects.
        """
        print(f"Resolving {url}")
        response = await self.session.head(
            url, allow_redirects=True, timeout=MAX_TIMEOUT
        )
        return str(response.url)

    @override
    async def download(self, url: str) -> list[dict[str, str]]:
        """
        Extracts and resolves all unique Bunkr album URLs from the given page.

        Fetches the HTML content of the specified URL, identifies all anchor
        tags with hrefs starting with "https://bunkr", removes duplicates, and
        resolves each to its final destination URL. Returns an empty list;
        downloading functionality is not yet implemented.

        Args:
            url (str): The URL of the page to scan for Bunkr album links.

        Returns:
            list[dict[str, str]]: Currently always returns an empty list.
        """
        soup: BeautifulSoup | None = await self.fetch_soup(url)
        if not soup:
            return []

        # Find all links that start with https://bunkrrr.org/a/
        urls: list[str] = [
            u["href"]
            for u in soup.find_all("a")
            if u["href"].startswith("https://bunkr")
        ]

        urls = list(set(urls))
        # Every url inside the list redirects to a different domain
        # so we need to resolve the real domain
        real_urls: list[str] = [await self.get_real_url(u) for u in urls]

        print(f"Found {len(real_urls)} albums on {url}")
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
