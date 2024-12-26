"""Downloader for https://wildskirts.com"""

import asyncio
from pathlib import Path

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import download_media_items, fetch_soup
from ososedki_dl.utils import get_final_path, main_entry

DOWNLOAD_URL = "https://wildskirts.com"
BASE_PHOTOS_URL = "https://photos.wildskirts.com"
BASE_VIDEOS_URL = "https://video.wildskirts.com"


def get_total_items(soup: BeautifulSoup, item: str) -> int:
    content_div: Tag | NavigableString | None = soup.find(
        "div", class_=f"text-center mx-4 cursor-pointer tab-{item}"
    )
    if not content_div:
        return 0

    paragraph: Tag | NavigableString | None | int = content_div.find("p")
    if not paragraph:
        return 0
    if isinstance(paragraph, int):
        return paragraph

    return int(paragraph.text)


def wildskirts_media_filter(soup: BeautifulSoup) -> list[str]:
    images: list = [
        image["src"]
        for image in soup.find_all("img")
        if BASE_PHOTOS_URL in image["src"]
        and "preview" not in image["src"]
        and "profile_photo" not in image["src"]
    ]
    videos: list = [
        video["src"]
        for video in soup.find_all("video")
        if BASE_VIDEOS_URL in video["src"] and not video["src"].endswith("#t=0.001")
    ]
    return images + videos


async def fetch_media_urls(session: ClientSession, url: str) -> list[str]:
    soup: BeautifulSoup | None = await fetch_soup(session, url)
    return wildskirts_media_filter(soup) if soup else []


@main_entry
async def download_profile(
    session: ClientSession,
    profile_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    # ! Beware, the trailing slash may return different results
    if profile_url.endswith("/"):
        profile_url = profile_url[:-1]

    profile: str = profile_url.split("/")[-1]

    soup: BeautifulSoup | None = await fetch_soup(session, profile_url)
    if not soup:
        return []

    total_pictures: int = get_total_items(soup, "photos")
    total_videos: int = get_total_items(soup, "videos")
    total_items: int = total_pictures + total_videos

    print(f"Total items: {total_items}")

    urls: list[str] = [f"{profile_url}/{i}" for i in range(1, total_items + 1)]
    # Fetch media URLs concurrently
    media_urls_lists: list[list[str]] = await asyncio.gather(
        *[fetch_media_urls(session, url) for url in urls]
    )
    # Flatten the list of lists into a single list
    media_urls: list[str] = [url for sublist in media_urls_lists for url in sublist]

    print("Retrieved media URLs")

    album_path: Path = get_final_path(download_path, profile)

    return await download_media_items(
        session=session,
        media_urls=media_urls,
        album_path=album_path,
        progress=progress,
        task=task,
    )
