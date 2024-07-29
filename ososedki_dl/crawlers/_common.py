import asyncio
from pathlib import Path
from typing import Callable

from aiohttp import ClientResponseError, ClientSession
from bs4 import BeautifulSoup
from rich import print
from rich.progress import Progress, TaskID

from ososedki_dl.utils import download_and_save_media, get_final_path, get_soup


async def fetch_soup(session: ClientSession, url: str) -> BeautifulSoup | None:
    print(f"Fetching {url}")
    try:
        return await get_soup(session, url)
    except ClientResponseError as e:
        print(f"Failed to fetch {url} with status {e.status}")
        return None


async def download_media_items(
    session: ClientSession,
    media_urls: list[str],
    album_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    tasks: list = [
        download_and_save_media(session=session, url=url, album_path=album_path)
        for url in media_urls
    ]

    results: list[dict[str, str]] = await asyncio.gather(*tasks)

    for _ in media_urls:
        progress.advance(task)

    return results


async def process_album(
    session: ClientSession,
    album_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
    title_extractor: Callable[[BeautifulSoup], str],
    media_filter: Callable[[BeautifulSoup], list[str]],
) -> list[dict[str, str]]:
    if album_url.endswith("/"):
        album_url = album_url[:-1]

    soup: BeautifulSoup = await fetch_soup(session, album_url)
    if soup is None:
        return []

    try:
        title: str = title_extractor(soup)
        media_urls: list = list(set(media_filter(soup)))
    except TypeError as e:
        # ? Handle soup corrupted or not as expected, retry soup fetching
        print(f"Failed to extract media URLs: {e}. Retrying...")
        return await process_album(
            session,
            album_url,
            download_path,
            progress,
            task,
            title_extractor,
            media_filter,
        )
    album_path: Path = get_final_path(download_path, title)

    return await download_media_items(
        session,
        media_urls,
        album_path,
        progress,
        task,
    )


def extract_images(html_page: BeautifulSoup, base_url: str) -> list[str]:
    return [img["src"] for img in html_page.find_all("img") if base_url in img["src"]]


def extract_videos(html_page: BeautifulSoup, base_url: str) -> list[str]:
    return [
        video["src"]
        for video in html_page.find_all("video")
        if base_url in video["src"]
    ]
