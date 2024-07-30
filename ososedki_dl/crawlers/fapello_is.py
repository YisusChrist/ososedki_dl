"""Downloader for https://fapello.is"""

from pathlib import Path

import requests  # type: ignore
from aiohttp import ClientSession
from rich import print
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import download_media_items
from ososedki_dl.utils import get_final_path

BASE_URL = "https://fapello.is//api/media"


async def download_profile(
    session: ClientSession,
    profile_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    if profile_url.endswith("/"):
        profile_url = profile_url[:-1]

    profile_id: str = profile_url.split("/")[-1]
    i = 1

    title: str = ""
    urls: list = []
    while True:
        url: str = f"{BASE_URL}/{profile_id}/{i}/1/0"
        print("Sending request to:", url)
        response: requests.Response = requests.get(url)
        if response.text == "null":
            break

        if not title:
            title = response.json()[0]["name"]
        album: list[dict] = response.json()
        urls += [media["newUrl"] for media in album if media["newUrl"]]
        i += 1

    album_path: Path = get_final_path(download_path, title)

    return await download_media_items(
        session=session,
        media_urls=urls,
        album_path=album_path,
        progress=progress,
        task=task,
    )
