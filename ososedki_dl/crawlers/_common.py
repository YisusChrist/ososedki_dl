"""Common functions for crawlers."""

import asyncio
import re
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import ParseResult, parse_qs, urlencode, urlparse

from aiohttp import ClientResponseError, ClientSession
from bs4 import BeautifulSoup, ResultSet  # type: ignore
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
    media_filter: Callable[[BeautifulSoup], list[str]],
    title_extractor: Optional[Callable[[BeautifulSoup], str]] = None,
    title: Optional[str] = None,
) -> list[dict[str, str]]:
    if album_url.endswith("/"):
        album_url = album_url[:-1]

    soup: BeautifulSoup = await fetch_soup(session, album_url)
    if soup is None:
        return []

    try:
        # Extract the title if a title_extractor is provided; otherwise, use the given title
        if title_extractor:
            title = title_extractor(soup)
        if not title:
            raise ValueError("Title could not be determined")

        media_urls: list = list(set(media_filter(soup)))
        print(f"Title: {title}")
        print(f"Media URLs: {len(media_urls)}")
        #input("Press Enter to continue...")
    except (TypeError, ValueError) as e:
        print(f"Failed to process album: {e}. Retrying...")
        return await process_album(
            session=session,
            album_url=album_url,
            download_path=download_path,
            progress=progress,
            task=task,
            media_filter=media_filter,
            title_extractor=title_extractor,
            title=title,
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


def search_ososedki_title(
    soup: BeautifulSoup, button_class: Optional[str] = None
) -> str:
    if button_class:
        button_html = soup.find("a", class_=button_class)
        if button_html:
            print(f"Found button: {button_html.text}")
            return button_html.text

    text_div = soup.find("title")
    text: str = text_div.text.strip()
    title: str = "Unknown"

    try:
        if " (@" in text:
            title = text.split(" (@")[0].strip()
        elif re.search(r" - [0-9]*\s", text):
            title = text.split(" - ")[0].strip()
    except IndexError:
        print(f"ERROR: Could not extract title from '{text}'")

    if title == "Unknown":
        title = _get_article_title(soup)

    return title


def search_ososedki_media(soup: BeautifulSoup, base_url: str) -> list[str]:
    # ? If images under a tag return 404, use tag img and get src
    images: list[str] = [
        tag.get("href").replace("/604/", "/1280/")
        for tag in soup.find_all("a", href=lambda href: base_url in href)
    ]
    if images:
        return images

    # ? If no images are found, search for "https://sun9-" in img_url
    for tag in soup.find_all("a", href=lambda href: href.startswith("https://sun")):
        href: str = tag.get("href")
        print(f"Found sun9 image: {href}")
        parsed_url: ParseResult = urlparse(href)
        query: dict[str, list[str]] = parse_qs(parsed_url.query, keep_blank_values=True)
        query.pop("cs", None)
        u: ParseResult = parsed_url._replace(query=urlencode(query, True))
        images.append(u.geturl())

    return images


def _get_article_title(soup: BeautifulSoup) -> str:
    tags: set[str] = {
        "leak",
        "leaked",
        "leaks",
        "nude",
        "nudes",
        "of",
        "onlyfans for",
        "onlyfans leak",
        "reddit",
        "twitter",
        "video",
        "vk",
        "xxx",
        "onlyfan",
        "onlyfanfor",
    }

    # Get the page article:tag and extract the title
    article_tags: ResultSet[str] = soup.find_all("meta", {"property": "article:tag"})
    for article_tag in article_tags:
        tag_content: str = article_tag.get("content", "")
        for tag in tags:
            tag_suffix: str = f" {tag.lower()}"
            if tag_content.lower().endswith(tag_suffix):
                return tag_content.replace(tag_suffix, "")

    return "Unknown"
