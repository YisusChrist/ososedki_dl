"""Downloader for https://husvjjal.blogspot.com"""

import ast
import json
from pathlib import Path

from aiohttp import ClientSession
from bs4 import BeautifulSoup  # type: ignore
from requests import Response, Session  # type: ignore
from requests_pprint import print_response_summary
import requests
from rich import print
from rich.progress import Progress, TaskID

from ._common import fetch_soup, process_album


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
    images: list[str] = []
    for tag in soup.find_all("a"):
        img_tag = tag.find("img")
        if not img_tag:
            continue

        # print(tag)
        if tag.get("href", "").strip().startswith("https://postimg.cc/"):
            value: str = tag.get("href", "").strip()
            if not value:
                continue
            images.append(value)
        else:
            value = img_tag.get("src", "").strip()
            if not value or not value.startswith("https://i.postimg.cc/"):
                continue
            images.append(value)

    videos: list[str] = [
        tag.get("src", "").strip()
        for tag in soup.find_all("iframe", class_="b-hbp-video b-uploaded")
    ]

    urls: list[str] = []
    with Session() as session:
        for img in images:
            if img.startswith("https://i.postimg.cc"):
                urls.append(img)
                continue
            soup = get_soup(session=session, url=img)
            download_link = soup.find(
                "a",
                {"id": "download"},
            )
            if download_link:
                urls.append(download_link["href"])

        for vid in videos:
            soup = get_soup(session=session, url=vid)
            js_script = soup.find(
                "script",
                {"type": "text/javascript"},
            )
            max_stream: dict[str, str] = get_max_stream(js_script.string)
            if not max_stream:
                continue
            urls.append(max_stream["play_url"])
            """
            response: Response = requests.get(max_stream["play_url"])
            response.raise_for_status()
            print_response_summary(response)
            with open("video.mp4", "wb") as f:
                f.write(response.content)
            """

    return urls


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

    print(albums)
    print(f"Total_albums: {len(albums)}")

    results = []
    for album in albums:
        results += await process_album(
            session=session,
            album_url=album,
            download_path=download_path,
            progress=progress,
            task=task,
            title_extractor=lambda _: "husvjjal",
            media_filter=husvjjal_blogspot_media_filter,
        )

    return results
