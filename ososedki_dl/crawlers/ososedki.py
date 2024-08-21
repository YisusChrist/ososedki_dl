"""Downloader for https://ososedki.com"""

from pathlib import Path

from aiohttp import ClientSession
from bs4 import BeautifulSoup  # type: ignore
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import process_album
from ososedki_dl.utils import main_entry

DOWNLOAD_URL = "https://ososedki.com"
BASE_URL = "https://ososedki.com/images/a/"


def ososedki_title_extractor(soup: BeautifulSoup) -> str:
    text_div = soup.find("div", class_="text-white container")
    text: str = text_div.text.strip()
    try:
        title: str = text.split("cosplay model ")[1].split(".")[0]
    except IndexError:
        try:
            title = text.split("Of course, ")[1].split(" is clearly over 18 years")[0]
        except IndexError:
            title = "Unknown"
    return title


def ososedki_media_filter(soup: BeautifulSoup) -> list[str]:
    # ? If images under a tag return 404, use tag img and get src
    # ? If no images are found, search for "https://sun9-" in img_url
    return [
        tag.get("href") for tag in soup.find_all("a") if BASE_URL in tag.get("href")
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
        title_extractor=ososedki_title_extractor,
        media_filter=ososedki_media_filter,
    )
