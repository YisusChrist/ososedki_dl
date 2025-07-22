"""Downloader for https://thefappening.plus"""

from pathlib import Path

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import process_album
from ososedki_dl.utils import main_entry

DOWNLOAD_URL = "https://thefappening.plus"
BASE_URL = DOWNLOAD_URL + "/photos"


def thefappening_plus_media_filter(soup: BeautifulSoup) -> list[str]:
    # Find all the images inside the div with the class 'gallery'
    return [
        img.get("src").replace("_s.", ".")
        for img in soup.find_all("img", class_="gallery_thumb")
        if img.get("src").startswith(BASE_URL)
    ]


@main_entry
async def download_album(
    session: ClientSession,
    model_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    if not model_url.endswith("/"):
        model_url += "/"

    return await process_album(
        session=session,
        album_url=model_url,
        download_path=download_path,
        progress=progress,
        task=task,
        title=model_url.split("/")[-2],
        media_filter=thefappening_plus_media_filter,
    )
