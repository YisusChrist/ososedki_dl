"""Downloader for https://cosplayasian.com"""

from pathlib import Path

from aiohttp import ClientSession
from bs4 import BeautifulSoup  # type: ignore
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import (process_album, search_ososedki_media,
                                          search_ososedki_title)
from ososedki_dl.utils import main_entry

DOWNLOAD_URL = "https://cosplayasian.com"
BASE_URL = "https://cosplayasian.com/images/a/"


def cosplayasian_title_extractor(soup: BeautifulSoup) -> str:
    return search_ososedki_title(soup=soup)


def cosplayasian_media_filter(soup: BeautifulSoup) -> list[str]:
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
        title_extractor=cosplayasian_title_extractor,
        media_filter=cosplayasian_media_filter,
    )
