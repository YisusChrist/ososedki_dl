"""Downloader for https://cosplaythots.com"""

from pathlib import Path

from aiohttp import ClientSession
from bs4 import BeautifulSoup  # type: ignore
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import (fetch_soup, process_model_album,
                                          search_ososedki_media,
                                          search_ososedki_title)
from ososedki_dl.utils import main_entry

DOWNLOAD_URL = "https://cosplaythots.com"
BASE_URL = DOWNLOAD_URL + "/images/a/"


def cosplaythots_title_extractor(soup: BeautifulSoup) -> str:
    return search_ososedki_title(soup=soup)


def cosplaythots_media_filter(soup: BeautifulSoup) -> list[str]:
    return search_ososedki_media(soup=soup, base_url=BASE_URL)


async def fetch_page_albums(session: ClientSession, page_url: str) -> list[str]:
    soup: BeautifulSoup | None = await fetch_soup(session, page_url)
    if not soup:
        return []

    # Find all links with format https://cosplaythots.com/p/
    albums: list[str] = [
        f"{DOWNLOAD_URL}{a["href"]}"
        for a in soup.find_all("a", href=lambda x: x and "/p/" in x)
    ]
    albums = list(set(albums))

    return albums


@main_entry
async def download_album(
    session: ClientSession,
    album_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    return await process_model_album(
        session=session,
        album_url=album_url,
        model_url=None,
        cosplay_url=f"{DOWNLOAD_URL}/c/",
        download_path=download_path,
        progress=progress,
        task=task,
        album_fetcher=fetch_page_albums,
        title_extractor=cosplaythots_title_extractor,
        media_filter=cosplaythots_media_filter,
    )
