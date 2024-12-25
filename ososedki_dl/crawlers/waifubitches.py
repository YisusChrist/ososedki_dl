"""Downloader for https://waifubitches.com"""

from pathlib import Path

from aiohttp import ClientSession
from bs4 import BeautifulSoup  # type: ignore
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import (fetch_soup, process_model_album,
                                          search_ososedki_media,
                                          search_ososedki_title)
from ososedki_dl.utils import main_entry

DOWNLOAD_URL = "https://waifubitches.com"
BASE_URL = "https://waifubitches.com/images/a/"


def waifubitches_title_extractor(soup: BeautifulSoup) -> str:
    return search_ososedki_title(soup=soup, button_class="btn btn-sm bg-pink-pink")


def waifubitches_media_filter(soup: BeautifulSoup) -> list[str]:
    return search_ososedki_media(soup=soup, base_url=BASE_URL)


async def fetch_page_albums(session: ClientSession, page_url: str) -> list[str]:
    soup: BeautifulSoup | None = await fetch_soup(session, page_url)
    if not soup:
        return []

    # Find all links that start with https://waifubitches.com/gallery/
    albums: list[str] = [
        f"{DOWNLOAD_URL}{a["href"]}"
        for a in soup.find_all("a", href=lambda x: x and x.startswith("/gallery/"))
    ]
    albums = list(set(albums))

    return albums


def get_model_name(soup: BeautifulSoup) -> str:
    return soup.find("title").text.split(" nude")[0].strip()


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
        model_url=f"{DOWNLOAD_URL}/model/",
        download_path=download_path,
        progress=progress,
        task=task,
        album_fetcher=fetch_page_albums,
        title_extractor=waifubitches_title_extractor,
        media_filter=waifubitches_media_filter,
    )
