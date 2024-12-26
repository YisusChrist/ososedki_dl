"""Downloader for https://bunkr-albums.io"""

from pathlib import Path

import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from rich import print
from rich.progress import Progress, TaskID

from ososedki_dl.consts import MAX_TIMEOUT
from ososedki_dl.crawlers._common import fetch_soup
from ososedki_dl.utils import main_entry

DOWNLOAD_URL = "https://bunkr-albums.io"


def get_real_url(url: str) -> str:
    print(f"Resolving {url}")
    response: requests.Response = requests.head(
        url, allow_redirects=True, timeout=MAX_TIMEOUT
    )
    return response.url


@main_entry
async def find_albums(
    session: ClientSession,
    url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    soup: BeautifulSoup | None = await fetch_soup(session, url)
    if not soup:
        return []

    # Find all links that start with https://bunkrrr.org/a/
    urls: list[str] = [
        u["href"]
        for u in soup.find_all("a")
        if u["href"].startswith("https://bunkrrr.org/a/")
    ]

    urls = list(set(urls))
    # Every url inside the list redirects to a different domain
    # so we need to resolve the real domain
    real_urls: list[str] = [get_real_url(u) for u in urls]

    print(f"Found {len(real_urls)} albums on {url}")
    print(real_urls)

    # TODO: Try to call the cyberdrop_dl program to download the albums

    return []


async def cyberdrop_dl(url: str, download_path: Path, real_urls: list[str]) -> None:
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
