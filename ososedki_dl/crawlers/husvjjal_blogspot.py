"""Downloader for https://husvjjal.blogspot.com"""

from pathlib import Path

from aiohttp import ClientSession
from bs4 import BeautifulSoup  # type: ignore
from rich.progress import Progress, TaskID
from requests import Response, Session  # type: ignore

from ._common import fetch_soup, process_album


def husvjjal_blogspot_media_filter(soup: BeautifulSoup) -> list[str]:
    images: list[str] = [
        tag.get("src", "").strip() or tag.get("href", "").strip()
        for tag in soup.find_all(["img", "a"])
        if (
            (
                tag.name == "img"
                and tag.get("src", "").strip().startswith("https://i.postimg.cc/")
            )
            or (
                tag.name == "a"
                and tag.get("href", "").strip().startswith("https://postimg.cc/")
            )
        )
    ]

    with Session() as session:
        for img in images:
            response: Response = session.get(img)
            soup = BeautifulSoup(response.text, "html.parser")
            download_link = soup.find("a", {"id": "download"})
            if download_link:
                # Pop the element from the list
                images.remove(img)
                images.append(download_link["href"])

    return images


async def download_profile(
    session: ClientSession,
    profile_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    if profile_url.endswith("/"):
        profile_url = profile_url[:-1]

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

    results: list[dict[str, str]] = []
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
