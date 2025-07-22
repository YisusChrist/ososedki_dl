"""Downloader for https://stripchat.com"""

from pathlib import Path

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import process_album
from ososedki_dl.utils import main_entry

DOWNLOAD_URL = "https://stripchat.com"
BASE_URL = "https://hls.strpst.com/records/"


def stripchat_media_filter(soup: BeautifulSoup) -> list[str]:
    # Find all the images inside the div with the class 'contentme'
    content_div: Tag | NavigableString | None = soup.find(
        "div", class_="videos-list-v2"
    )
    if not content_div or isinstance(content_div, NavigableString):
        return []
    return [
        img.get("src")
        for img in content_div.find_all("img")
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
    if model_url.endswith("/"):
        model_url = model_url[:-1]

    if not model_url.endswith("/videos"):
        return []

    # TODO: Need to bypass cloudflare in order to fetch the page
    return await process_album(
        session=session,
        album_url=model_url,
        download_path=download_path,
        progress=progress,
        task=task,
        title=model_url.split("/")[-2],
        media_filter=stripchat_media_filter,
    )
