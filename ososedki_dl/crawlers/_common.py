"""Common functions for crawlers."""

import asyncio
import re
from pathlib import Path
from typing import (Any, AsyncGenerator, Awaitable, Callable, Coroutine,
                    Optional)
from urllib.parse import ParseResult, parse_qs, urlencode, urlparse

from aiohttp import ClientResponseError, ClientSession
from bs4 import BeautifulSoup, ResultSet
from bs4.element import NavigableString, Tag
from rich import print
from rich.progress import Progress, TaskID

from ososedki_dl.download import download_and_save_media, get_soup
from ososedki_dl.utils import get_final_path


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

    soup: BeautifulSoup | None = await fetch_soup(session, album_url)
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


def search_ososedki_title(
    soup: BeautifulSoup, button_class: Optional[str] = None
) -> str:
    if button_class:
        button_html: Tag | NavigableString | None = soup.find("a", class_=button_class)
        if button_html:
            print(f"Found button: {button_html.text}")
            return button_html.text

    text_div: Tag | NavigableString | None = soup.find("title")
    if not text_div:
        return "Unknown"

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
    article_tags: ResultSet[Any] = soup.find_all("meta", {"property": "article:tag"})
    for article_tag in article_tags:
        tag_content: str = article_tag.get("content", "")
        for tag in tags:
            tag_suffix: str = f" {tag.lower()}"
            if tag_content.lower().endswith(tag_suffix):
                return tag_content.replace(tag_suffix, "")

    return "Unknown"


async def fetch_page_albums(
    session: ClientSession,
    page_url: str,
    album_href_filter: Callable[[str], bool],
    download_url: str,
) -> list[str]:
    soup: BeautifulSoup | None = await fetch_soup(session, page_url)
    if not soup:
        return []

    albums: list[str] = [
        f"{download_url}{a['href']}" for a in soup.find_all("a", href=album_href_filter)
    ]
    return list(set(albums))


async def find_model_albums(
    session: ClientSession,
    model_url: str,
    album_fetcher: Callable[[ClientSession, str], Awaitable[list[str]]],
    title_extractor: Callable[[BeautifulSoup], str],
) -> AsyncGenerator[tuple[list[str], str], None]:
    # Clean the URL removing the query parameters
    model_url = model_url.split("?")[0]

    soup: BeautifulSoup | None = await fetch_soup(session, model_url)
    if not soup:
        return

    model_name: str = title_extractor(soup)
    i = 1
    albums_found = True

    while albums_found:
        page_url: str = f"{model_url}?page={i}"
        albums_extracted: list[str] = await album_fetcher(session, page_url)
        if not albums_extracted:
            albums_found = False
            continue

        yield albums_extracted, model_name
        i += 1

        # Sleep for a while to avoid being banned
        await asyncio.sleep(1)


async def process_model_album(
    session: ClientSession,
    album_url: str,
    model_url: Optional[str],
    cosplay_url: Optional[str],
    download_path: Path,
    progress: Progress,
    task: TaskID,
    album_fetcher: Callable[[ClientSession, str], Awaitable[list[str]]],
    title_extractor: Callable[[BeautifulSoup], str],
    media_filter: Callable[[BeautifulSoup], list[str]],
) -> list[dict[str, str]]:
    if (model_url and album_url.startswith(model_url)) or (
        cosplay_url and album_url.startswith(cosplay_url)
    ):
        results: list[dict[str, str]] = []

        # Find all the albums for the model incrementally
        async for albums, model in find_model_albums(
            session=session,
            model_url=album_url,
            album_fetcher=album_fetcher,
            title_extractor=title_extractor,
        ):
            tasks: list[Coroutine[Any, Any, list[dict[str, str]]]] = [
                process_album(
                    session=session,
                    album_url=album,
                    download_path=download_path,
                    progress=progress,
                    task=task,
                    media_filter=media_filter,
                    title_extractor=title_extractor,
                )
                for album in albums
            ]

            # Process the tasks for this chunk and collect results
            chunk_results: list[dict[str, str]] = sum(await asyncio.gather(*tasks), [])
            results.extend(chunk_results)

        return results

    return await process_album(
        session=session,
        album_url=album_url,
        download_path=download_path,
        progress=progress,
        task=task,
        media_filter=media_filter,
        title_extractor=title_extractor,
    )
