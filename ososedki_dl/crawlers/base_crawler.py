"""Base crawler for ososedki and clone sites."""

import asyncio
import re
from abc import ABC
from typing import (Any, AsyncGenerator, Awaitable, Callable, Coroutine,
                    Optional)
from urllib.parse import ParseResult, parse_qs, urlencode, urlparse

from aiohttp import ClientSession
from bs4 import BeautifulSoup, ResultSet
from bs4.element import NavigableString, Tag
from core_helpers.logs import logger
from rich import print

from ..download import SessionType
from ._common import CrawlerContext, fetch_soup, process_album


class BaseCrawler(ABC):
    """Base class for crawlers of ososedki and clone sites."""

    site_url: str
    base_image_path: str
    album_path: Optional[str] = None
    model_url: Optional[str] = None
    cosplay_url: Optional[str] = None
    button_class: Optional[str] = None

    def __init__(self) -> None:
        logger.debug(
            f"Initialized {self.__class__.__name__} with site URL: {self.site_url}"
        )
        self.base_media_url: str = self.site_url + self.base_image_path

    async def fetch_page_albums(
        self, session: ClientSession, page_url: str
    ) -> list[str]:
        logger.debug(f"Fetching albums from page: {page_url}")

        if not self.album_path:
            logger.warning(
                f"Album path is not set for {self.__class__.__name__}. Skipping album fetch."
            )
            return []

        soup: BeautifulSoup | None = await fetch_soup(session, page_url)
        if not soup:
            logger.error(f"Failed to fetch or parse page: {page_url}")
            return []

        logger.debug(f"Extracting albums from soup for {self.__class__.__name__}")
        return list(
            {
                f"{self.site_url}{a['href']}"
                for a in soup.find_all("a", href=lambda x: x and self.album_path in x)
            }
        )

    def _get_article_title(self, soup: BeautifulSoup) -> str:
        logger.debug("Extracting article title from soup")

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
        article_tags: ResultSet[Any] = soup.find_all(
            "meta", {"property": "article:tag"}
        )
        for article_tag in article_tags:
            tag_content: str = article_tag.get("content", "")
            for tag in tags:
                tag_suffix: str = f" {tag.lower()}"
                if tag_content.lower().endswith(tag_suffix):
                    logger.info(f"Found article tag: {tag_content}")
                    return tag_content.replace(tag_suffix, "")

        logger.warning(
            f"No suitable article tag found in the soup for {self.__class__.__name__}"
        )
        return "Unknown"

    def extract_title(self, soup: BeautifulSoup) -> str:
        logger.debug("Extracting title from soup")

        title: str = "Unknown"

        if self.button_class:
            button_html: Tag | NavigableString | None = soup.find(
                "a", class_=self.button_class
            )
            if button_html:
                logger.info(f"Found button with class '{self.button_class}'")
                print(f"Found button: {button_html.text}")
                return button_html.text

        text_div: Tag | NavigableString | None = soup.find("title")
        if not text_div:
            logger.warning(f"No title found in the soup for {self.__class__.__name__}")
            return title
        text: str = text_div.text.strip()

        try:
            if " (@" in text:
                title = text.split(" (@")[0].strip()
            elif re.search(r" - [0-9]*\s", text):
                title = text.split(" - ")[0].strip()
        except IndexError:
            logger.error(f"Error extracting title from '{text}'")
            print(f"ERROR: Could not extract title from '{text}'")

        if title == "Unknown":
            title = self._get_article_title(soup)

        logger.info(f"Extracted title: {title}")
        return title

    def extract_media(self, soup: BeautifulSoup) -> list[str]:
        logger.debug("Extracting media from soup")

        # ? If images under a tag return 404, use tag img and get src
        images: list[str] = [
            tag.get("href").replace("/604/", "/1280/")
            for tag in soup.find_all("a", href=lambda href: self.base_media_url in href)
        ]
        if images:
            logger.info(f"Found {len(images)} images in the soup")
            return images

        logger.warning("No images found in the soup, searching for alternative sources")
        # ? If no images are found, search for "https://sun9-" in img_url
        for tag in soup.find_all("a", href=lambda href: href.startswith("https://sun")):
            href: str = tag.get("href")
            print(f"Found sun9 image: {href}")
            parsed_url: ParseResult = urlparse(href)
            query: dict[str, list[str]] = parse_qs(
                parsed_url.query, keep_blank_values=True
            )
            query.pop("cs", None)
            u: ParseResult = parsed_url._replace(query=urlencode(query, True))
            images.append(u.geturl())

        logger.info(f"Found {len(images)} images after alternative search")
        return images

    async def _find_model_albums(
        self,
        session: SessionType,
        model_url: str,
        album_fetcher: Callable[[SessionType, str], Awaitable[list[str]]],
        title_extractor: Callable[[BeautifulSoup], str],
    ) -> AsyncGenerator[tuple[list[str], str], None]:
        logger.debug(f"Finding model albums for URL: {model_url}")

        # Clean the URL removing the query parameters
        model_url = model_url.split("?")[0]

        soup: BeautifulSoup | None = await fetch_soup(session, model_url)
        if not soup:
            logger.error(f"Failed to fetch or parse model page: {model_url}")
            return

        model_name: str = title_extractor(soup)
        i = 1
        albums_found = True

        while albums_found:
            page_url: str = f"{model_url}?page={i}"
            logger.debug("Fetching albums from page %s", page_url)
            albums_extracted: list[str] = await album_fetcher(session, page_url)
            if not albums_extracted:
                albums_found = False
                continue

            logger.info(f"Found {len(albums_extracted)} albums on page {page_url}")
            yield albums_extracted, model_name
            i += 1

            # Sleep for a while to avoid being banned
            await asyncio.sleep(1)

        logger.debug(f"Finished finding albums for model: {model_name}")

    async def download(self, context: CrawlerContext, url: str) -> list[dict[str, str]]:
        logger.debug(f"Downloading from URL {url} using {self.__class__.__name__}")

        if (self.model_url and url.startswith(self.model_url)) or (
            self.cosplay_url and url.startswith(self.cosplay_url)
        ):
            logger.info(f"Downloading albums for model or cosplay from {url}")
            results: list[dict[str, str]] = []

            # Find all the albums for the model incrementally
            async for albums, _ in self._find_model_albums(
                context.session, url, self.fetch_page_albums, self.extract_title
            ):
                tasks: list[Coroutine[Any, Any, list[dict[str, str]]]] = [
                    process_album(
                        context, album, self.extract_media, self.extract_title
                    )
                    for album in albums
                ]

                # Process the tasks for this chunk and collect results
                chunk_results: list[dict[str, str]] = sum(
                    await asyncio.gather(*tasks), []
                )
                results.extend(chunk_results)

            return results

        logger.info(f"Downloading album from {url} using {self.__class__.__name__}")
        return await process_album(context, url, self.extract_media, self.extract_title)
