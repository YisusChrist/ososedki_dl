"""Downloader for https://ososedki.com"""

from pathlib import Path

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import (process_album, search_ososedki_media,
                                          search_ososedki_title)
from ososedki_dl.utils import main_entry

DOWNLOAD_URL = "https://ososedki.com"
BASE_URL = DOWNLOAD_URL + "/images/a/"


def ososedki_title_extractor(soup: BeautifulSoup) -> str:
    return search_ososedki_title(soup=soup)


def ososedki_media_filter(soup: BeautifulSoup) -> list[str]:
    return search_ososedki_media(soup=soup, base_url=BASE_URL)


@main_entry
async def download_album(
    session: ClientSession,
    album_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    return await process_album(
        session=session,
        album_url=album_url,
        download_path=download_path,
        progress=progress,
        task=task,
        title_extractor=ososedki_title_extractor,
        media_filter=ososedki_media_filter,
    )
