"""Downloader for https://cosxuxi.club"""

from pathlib import Path

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import download_media_items, fetch_soup
from ososedki_dl.utils import get_final_path, main_entry

DOWNLOAD_URL = "https://cosxuxi.club"
BASE_URL = ".wp.com/img.nungvl.net/"


def cosxuxi_club_title_extractor(soup: BeautifulSoup) -> str:
    text_div: Tag | NavigableString | None = soup.find("title")
    if not text_div:
        return "Unknown"
    text: str = text_div.text.strip()
    title: str = "Unknown"
    try:
        if "CosXuxi Club: " in text and " - " in text:
            title = text.split("CosXuxi Club: ")[1].split(" - ")[0].strip()
    except IndexError:
        print(f"ERROR: Could not extract title from '{text}'")
    return title


def cosxuxi_club_media_filter(soup: BeautifulSoup) -> list[str]:
    # Find all the images inside the div with the class 'contentme'
    content_div: Tag | NavigableString | None = soup.find("div", class_="contentme")
    if not content_div or isinstance(content_div, NavigableString):
        return []

    return [
        img.get("src")
        for img in content_div.find_all("img")
        if BASE_URL in img.get("src")
    ]


@main_entry
async def download_album(
    session: ClientSession,
    album_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    if album_url.endswith("/"):
        album_url = album_url[:-1]

    title: str = ""
    urls: list[str] = []
    url: str = album_url

    while True:
        soup: BeautifulSoup | None = await fetch_soup(session, url)
        if not soup:
            break
        page_urls: list[str] = cosxuxi_club_media_filter(soup) if soup else []
        if not page_urls:
            break

        urls.extend(page_urls)

        if not title:
            title = cosxuxi_club_title_extractor(soup)

        # Check if there is a next page
        next_page: Tag | None = soup.find("a", class_="page-numbers", string="Next >")
        if not next_page or not next_page.get("href"):
            break
        next_page_url: str | list[str] = next_page.get("href", "")
        if isinstance(next_page_url, list):
            next_page_url = next_page_url[0]
        url = DOWNLOAD_URL + next_page_url

    album_path: Path = get_final_path(download_path, title)

    return await download_media_items(
        session=session,
        media_urls=urls,
        album_path=album_path,
        progress=progress,
        task=task,
    )
