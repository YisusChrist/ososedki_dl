"""Downloader for https://cosplayboobs.com"""

import asyncio
from pathlib import Path
from time import sleep

from aiohttp import ClientSession
from bs4 import BeautifulSoup  # type: ignore
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import (fetch_soup, process_album,
                                          search_ososedki_media,
                                          search_ososedki_title)
from ososedki_dl.utils import main_entry

DOWNLOAD_URL = "https://cosplayboobs.com"
BASE_URL = "https://cosplayboobs.com/images/a/"


def cosplayboobs_title_extractor(soup: BeautifulSoup) -> str:
    return search_ososedki_title(soup=soup, button_class="btn btn-sm bg-model")


def cosplayboobs_media_filter(soup: BeautifulSoup) -> list[str]:
    return search_ososedki_media(soup=soup, base_url=BASE_URL)


async def fetch_page_albums(session: ClientSession, page_url: str) -> list[str]:
    soup: BeautifulSoup | None = await fetch_soup(session, page_url)
    if not soup:
        return []

    # Find all links with format https://cosplayboobs.com/xx/album/
    albums: list[str] = [
        f"{DOWNLOAD_URL}{a["href"]}"
        for a in soup.find_all(
            "a", href=lambda x: x and "/album/" in x
        )
    ]
    albums = list(set(albums))

    return albums

async def find_model_albums(
    session: ClientSession, model_url: str
) -> tuple[list[str], str]:
    # Clean the URL removing the query parameters
    model_url = model_url.split("?")[0]

    soup: BeautifulSoup | None = await fetch_soup(session, model_url)
    if not soup:
        return [], ""
    model_name: str = get_model_name(soup)

    albums: list[str] = []
    albums_found = True
    i = 1

    while albums_found:
        page_url: str = f"{model_url}?page={i}"
        albums_extracted: list[str] = await fetch_page_albums(session, page_url)
        if not albums_extracted:
            albums_found = False
            break

        albums.extend(albums_extracted)
        i += 1
        sleep(0.5)

    return albums, model_name


def get_model_name(soup: BeautifulSoup) -> str:
    return soup.find("title").text.split(" nude")[0].strip()


@main_entry
async def download_album(
    session: ClientSession,
    album_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    if "/model/" in album_url:
        # Find all the albums for the model
        albums, model = await find_model_albums(session, album_url)

        tasks: list = [
            process_album(
                session=session,
                album_url=album,
                download_path=download_path,
                progress=progress,
                task=task,
                media_filter=cosplayboobs_media_filter,
                title=model,
            )
            for album in albums
        ]

        results: list[dict[str, str]] = await asyncio.gather(*tasks)
        return results


    return await process_album(
        session=session,
        album_url=album_url,
        download_path=download_path,
        progress=progress,
        task=task,
        title_extractor=cosplayboobs_title_extractor,
        media_filter=cosplayboobs_media_filter,
    )
