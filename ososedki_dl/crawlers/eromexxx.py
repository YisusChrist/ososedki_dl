"""Downloader for https://eromexxx.com"""

from pathlib import Path

import tldextract
from aiohttp import ClientResponseError, ClientSession
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from rich import print
from rich.progress import Progress, TaskID

from ososedki_dl.download import download_and_save_media, get_soup
from ososedki_dl.utils import get_final_path, main_entry

DOWNLOAD_URL = "https://eromexxx.com"


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

    profile: str = profile_url.split("/")[-1]

    soup: BeautifulSoup = await get_soup(session, profile_url)

    # Get the total number of albums
    header: Tag | NavigableString | None = soup.find("div", class_="header-title")
    if not header:
        return []
    span: Tag | NavigableString | None | int = header.find("span")
    if not span or isinstance(span, int):
        return []
    total_albums = int(span.text.split(" ")[1])
    print(f"Total_albums: {total_albums}")

    # Get all album URLs from pagination
    albums: list = await find_albums_with_pagination(session, profile_url, profile)

    # Determine the highest album offset
    highest_offset: int = max(
        int(album.split("-")[-1].split("/")[0]) for album in albums
    )
    print(f"Highest_offset: {highest_offset}")
    base_url: str = "".join(profile_url.split("/model"))

    results: list[dict[str, str]] = []
    for i in range(1, highest_offset + 1):
        results += await download_album(
            session=session,
            album_url=f"{base_url}-{i}",
            title=profile,
            download_path=download_path,
            progress=progress,
            task=task,
        )

    return results


async def find_albums_with_pagination(
    session: ClientSession, profile_url: str, profile: str
) -> list:
    soup: BeautifulSoup = await get_soup(session, profile_url)
    # Get pagination items
    pagination: Tag | NavigableString | None = soup.find("ul", class_="pagination")
    if not pagination or isinstance(pagination, NavigableString):
        return []
    # Get the last page number
    try:
        last_page = int(pagination.find_all("li")[-2].text)
    except AttributeError:
        # Only one page, return the current page
        last_page = 1

    albums: list = []
    for page in range(1, last_page + 1):
        page_url: str = f"{profile_url}/page/{page}"
        page_soup: BeautifulSoup = await get_soup(session, page_url)
        page_albums: list = find_albums_in_soup(page_soup, profile)
        albums.extend(page_albums)

    albums = list(set(albums))  # Remove duplicates
    return albums


def find_albums_in_soup(soup: BeautifulSoup, profile: str) -> list:
    albums: list = []
    for album in soup.find_all("a", class_="athumb thumb-link"):
        if profile in album["href"]:
            albums.append(album["href"])
    return albums


async def download_album(
    session: ClientSession,
    album_url: str,
    title: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    try:
        soup: BeautifulSoup = await get_soup(session, album_url)
    except ValueError:
        return []
    except ClientResponseError as e:
        print(f"Failed to fetch {album_url} with status {e.status}")
        return []

    videos: list = [video_source["src"] for video_source in soup.find_all("source")]
    images: list = [
        image["data-src"] for image in soup.find_all("img", class_="img-back lazyload")
    ]
    urls = list(set(images + videos))

    album_path: Path = get_final_path(download_path, title)

    results: list[dict[str, str]] = []
    for url in urls:
        result: dict[str, str] = await download(
            session=session,
            url=url,
            download_path=album_path,
            album=album_url,
        )
        results.append(result)
        progress.advance(task)

    return results


async def download(
    session: ClientSession, url: str, download_path: Path, album: str = ""
) -> dict[str, str]:
    hostname: str = tldextract.extract(url).fqdn

    headers: dict[str, str] = {
        "Referer": album or f"https://{hostname}",
        "Origin": f"https://{hostname}",
        "User-Agent": "Mozila/5.0",
    }

    return await download_and_save_media(
        session,
        url,
        download_path,
        headers,
    )
