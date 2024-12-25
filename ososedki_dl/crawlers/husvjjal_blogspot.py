"""Downloader for https://husvjjal.blogspot.com"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from aiohttp import ClientSession
from bs4 import BeautifulSoup  # type: ignore
from requests import Response, Session  # type: ignore
from rich import print
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import fetch_soup, process_album
from ososedki_dl.download import fetch
from ososedki_dl.utils import main_entry

DOWNLOAD_URL = "https://husvjjal.blogspot.com"


@lru_cache
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
        title_extractor=lambda _: "husvjjal",
        media_filter=husvjjal_blogspot_media_filter,
    )


async def get_related_albums(session: ClientSession, album_url: str) -> list[str]:
    print(f"Fetching related albums for {album_url}")

    headers: dict[str, str] = {"Referer": album_url}

    js_url = "https://husvjjal.blogspot.com/feeds/posts/default"
    params: dict[str, str] = {
        "alt": "json-in-script",
        "callback": "BloggerJS.related",
        "max-results": "12",
        "q": 'label:"Video"',
    }

    js_script: str = await fetch(
        session=session, url=js_url, headers=headers, params=params
    )
    script_json: str = js_script.split("BloggerJS.related(")[1].split(");")[0].strip()
    # Convert the str to a dictionary
    js_dict: dict[str, Any] = json.loads(script_json)

    js_feed_entry: list[dict] = js_dict["feed"]["entry"]

    related_albums: list[str] = []
    for entry in js_feed_entry:
        entry_link: list[dict] = entry["link"]
        for link in entry_link:
            if link["rel"] == "alternate" and link["type"] == "text/html":
                related_albums.append(link["href"])
                break

    return related_albums


def get_soup(session: Session, url: str) -> BeautifulSoup:
    response: Response = session.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_max_stream(js_script: str) -> dict[str, str]:
    if not js_script:
        print("No js_script found")
        return {}

    video_config_str: str = (
        js_script.split("var VIDEO_CONFIG = ")[1].split(";")[0].strip()
    )
    # Convert the video config to a dictionary
    video_config: dict = json.loads(video_config_str)

    # Find the one with the highest format_id
    max_stream: dict = max(video_config["streams"], key=lambda x: x["format_id"])
    if not max_stream:
        print("No max stream found")
        return {}

    return max_stream


def husvjjal_blogspot_media_filter(soup: BeautifulSoup) -> list[str]:
    # Define allowed hostnames
    allowed_img_hostnames: set[str] = {"i.postimg.cc", "postimg.cc"}

    images: list[str] = []
    for tag in soup.find_all("a"):
        img_tag = tag.find("img")
        if not img_tag:
            continue

        href: str = tag.get("href", "").strip()
        src: str = img_tag.get("src", "").strip()

        # Parse the URL to check the hostname
        href_hostname: str | None = urlparse(href).hostname
        src_hostname: str | None = urlparse(src).hostname

        if href_hostname and href_hostname in allowed_img_hostnames:
            images.append(href)
        elif src_hostname and src_hostname in allowed_img_hostnames:
            images.append(src)

    videos: list[str] = [
        tag.get("src", "").strip()
        for tag in soup.find_all("iframe", class_="b-hbp-video b-uploaded")
    ]

    urls: list[str] = []
    with Session() as session:
        for img in images:
            img_hostname: str | None = urlparse(img).hostname
            if img_hostname and img_hostname == "i.postimg.cc":
                urls.append(img)
                continue
            soup = get_soup(session=session, url=img)
            download_link = soup.find(
                "a",
                {"id": "download"},
            )
            if download_link:
                download_href: str = download_link.get("href", "").strip()
                download_hostname: str | None = urlparse(download_href).hostname
                if download_hostname and download_href.startswith("https://"):
                    urls.append(download_href)

        for vid in videos:
            soup = get_soup(session=session, url=vid)
            js_script = soup.find(
                "script",
                {"type": "text/javascript"},
            )
            max_stream: dict[str, str] = get_max_stream(js_script.string)
            if not max_stream:
                continue
            play_url: str = max_stream.get("play_url", "").strip()
            play_hostname: str | None = urlparse(play_url).hostname
            if play_hostname and play_url.startswith("https://"):
                urls.append(play_url)

    return urls


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

    if profile_url.endswith(".html"):
        results: list[dict[str, str]] = await process_album(
            session=session,
            album_url=profile_url,
            download_path=download_path,
            progress=progress,
            task=task,
            title_extractor=lambda _: "husvjjal",
            media_filter=husvjjal_blogspot_media_filter,
        )
        related_albums: list[str] = await get_related_albums(
            session,
            profile_url,
        )
        for related_album in related_albums:
            results += await process_album(
                session=session,
                album_url=related_album,
                download_path=download_path,
                progress=progress,
                task=task,
                title_extractor=lambda _: "husvjjal",
                media_filter=husvjjal_blogspot_media_filter,
            )
        return results

    soup: BeautifulSoup = await fetch_soup(session, profile_url)

    album_classes: list[str] = [
        "card-image ratio o-hidden mask ratio-16:9",
        "gallery-name fw-500 font-primary fs-5 l:fs-3",
        "gallery ratio mask carousel-cell gallery-default ratio-4:3",
        "gallery ratio mask carousel-top gallery-featured ratio-16:9",
    ]

    albums_html = soup.find_all("a", class_=album_classes)
    albums = list(set([album["href"] for album in albums_html]))

    results = []
    index = 0
    while index < len(albums):
        album: str = albums[index]
        results += await download_album(
            session=session,
            album_url=album,
            download_path=download_path,
            progress=progress,
            task=task,
        )
        related_albums = await get_related_albums(session, album)
        for related_album in related_albums:
            if related_album not in albums:
                albums.append(related_album)

        index += 1  # Move to the next album in the list

    return results
