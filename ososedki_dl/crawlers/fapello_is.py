"""Downloader for https://fapello.is"""

from pathlib import Path

from aiohttp import ClientSession
from rich import print
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import download_media_items
from ososedki_dl.utils import get_final_path, main_entry

DOWNLOAD_URL = "https://fapello.is"
BASE_URL = DOWNLOAD_URL + "//api/media"


async def fetch_media_urls(session: ClientSession, url: str) -> list[dict] | str:
    async with session.get(url) as response:
        if response.status != 200:
            return []
        return await response.json()


@main_entry
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
    print(f"Fetching data from profile {profile_id}...")
    while True:
        url: str = f"{BASE_URL}/{profile_id}/{i}/1/0"
        album: list[dict] | str = await fetch_media_urls(session, url)
        if not album or album == "null":
            break

        if isinstance(album, str):
            print("Error fetching album:", album)
            break

        if not title:
            title = album[0]["name"]
        urls += [media["newUrl"] for media in album if media["newUrl"]]
        i += 1

    print(f"Found {len(urls)} media items in profile {profile_id}")

    album_path: Path = get_final_path(download_path, title)

    return await download_media_items(
        session=session,
        media_urls=urls,
        album_path=album_path,
        progress=progress,
        task=task,
    )
