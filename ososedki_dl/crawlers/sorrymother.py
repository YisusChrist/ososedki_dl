"""Downloader for https://sorrymother.to"""

from pathlib import Path

from aiohttp import ClientSession
from bs4 import BeautifulSoup  # type: ignore
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import process_album
from ososedki_dl.utils import main_entry

DOWNLOAD_URL = "https://sorrymother.to"
BASE_URL = "https://pics.sorrymother.video/"


def sorrymother_title_extractor(soup: BeautifulSoup) -> str:
    # TODO: Add a better way to get the title, this fails if there is no tag
    # or if the first tag is not the correct title
    tags = soup.find_all("a", {"class": "entry-tag"})
    return tags[0].text if tags else "Untitled"


def sorrymother_media_filter(soup: BeautifulSoup) -> list[str]:
    images_list: list = [
        img["src"] for img in soup.find_all("img") if BASE_URL in img["src"]
    ]
    # Remove the resolution from the image name
    images: list[str] = []
    for image in images_list:
        parts: list[str] = image.split("-")
        new_name: str = "-".join(parts[:-1]) + "." + parts[-1].split(".")[-1]
        images.append(new_name)
    videos: list = [
        video["src"].split("?")[0]
        for video in soup.find_all("source", {"type": "video/mp4"})
    ]
    return images + videos


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
        title_extractor=sorrymother_title_extractor,
        media_filter=sorrymother_media_filter,
    )
