"""Downloader for https://waifubitches.com"""

from pathlib import Path

from aiohttp import ClientSession
from bs4 import BeautifulSoup  # type: ignore
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import process_album
from ososedki_dl.utils import main_entry

DOWNLOAD_URL = "https://waifubitches.com"
BASE_URL = "https://waifubitches.com/images/a/"


def waifubitches_title_extractor(soup: BeautifulSoup) -> str:
    text_div = soup.find("title")
    text: str = text_div.text.strip()
    try:
        if " (" in text:
            title: str = text.split("(")[0].strip()
        elif " - " in text:
            title = text.split(" - ")[0].strip()
    except IndexError:
        print("Error: ", text)
        raise
        title = "Unknown"
    return title


def waifubitches_media_filter(soup: BeautifulSoup) -> list[str]:
    # ? If images under a tag return 404, use tag img and get src
    # ? If no images are found, search for "https://sun9-" in img_url
    return [
        tag.get("href").replace("/604/", "/1280/")
        for tag in soup.find_all("a")
        if BASE_URL in tag.get("href")
    ]


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
        title_extractor=waifubitches_title_extractor,
        media_filter=waifubitches_media_filter,
    )
