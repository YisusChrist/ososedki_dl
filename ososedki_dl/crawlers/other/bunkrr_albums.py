"""Downloader for https://bunkr-albums.io"""

from pathlib import Path
from typing import override

from bs4 import BeautifulSoup
from rich import print

from ...consts import MAX_TIMEOUT
from .._common import fetch_soup
from ..simple_crawler import SimpleCrawler


class BunkrAlbumsCrawler(SimpleCrawler):
    site_url = "https://bunkr-albums.io"

    async def get_real_url(self, url: str) -> str:
        print(f"Resolving {url}")
        response = await self.context.session.head(
            url, allow_redirects=True, timeout=MAX_TIMEOUT
        )
        return response.url

    @override
    async def download(self, url: str) -> list[dict[str, str]]:
        soup: BeautifulSoup | None = await fetch_soup(self.context.session, url)
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
        #real_urls: list[str] = [await self.get_real_url(u) for u in urls]

        print(f"Found {len(urls)} albums on {url}")
        print(urls)

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
