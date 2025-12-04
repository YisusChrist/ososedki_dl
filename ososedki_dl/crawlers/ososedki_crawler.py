"""Base crawler for ososedki and clone sites."""

from __future__ import annotations

import asyncio
import re
from abc import ABC
from itertools import chain
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlencode, urlparse

from bs4 import BeautifulSoup, Tag
from core_helpers.logs import logger
from rich import print
from typing_extensions import override

from ..consts import DEFAULT_ALBUM_TITLE, DEFAULT_PAGINATION_SIZE, MAX_TIMEOUT
from .base_crawler import BaseCrawler

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable
    from types import CoroutineType
    from typing import Any
    from urllib.parse import ParseResult

    from bs4 import NavigableString, ResultSet


class OsosedkiBaseCrawler(BaseCrawler, ABC):
    """Base class for crawlers of ososedki and clone sites."""

    album_path: str
    model_url: str | None = None
    cosplay_url: str | None = None
    fandom_url: str | None = None
    button_class: str | None = None
    pagination: bool

    async def fetch_page_albums(self, page_url: str) -> list[str]:
        """
        Asynchronously fetches a page and returns a list of unique album URLs
        found on that page.

        Args:
            page_url (str): The URL of the page to fetch.

        Returns:
            list[str]: A list of absolute album URLs extracted from anchor tags
            whose href starts with the configured album path. Returns an empty
            list if the page cannot be fetched or no albums are found.
        """
        logger.debug(f"Fetching albums from page: {page_url}")
        soup: BeautifulSoup | None = await self.fetch_soup(page_url)
        if not soup:
            return []

        if not self.album_path:
            logger.warning(
                f"Album path is not set for {self.__class__.__name__}. Skipping album fetch."
            )

        logger.debug(f"Extracting albums from soup for {self.__class__.__name__}")
        return list(
            {
                f"{self.site_url}{a['href']}"
                for a in soup.find_all(
                    "a", href=lambda href: href and href.startswith(self.album_path)
                )
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
        return DEFAULT_ALBUM_TITLE

    def extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extracts the title of an album or model page from the provided
        BeautifulSoup object.

        Attempts to find a title by checking for an anchor tag with a specific
        button class, parsing the "title" tag for known patterns, or falling
        back to meta tags. Returns `DEFAULT_ALBUM_TITLE` if no suitable title is
        found.

        Args:
            soup (BeautifulSoup): Parsed HTML content of the page.

        Returns:
            str: The extracted title of the album or model, or
                `DEFAULT_ALBUM_TITLE` if no title could be extracted.
        """
        logger.debug("Extracting title from soup")

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
            logger.warning(
                f"No title tag found in the soup for {self.__class__.__name__}"
            )
            return DEFAULT_ALBUM_TITLE

        text: str = text_div.text.strip()
        title: str = DEFAULT_ALBUM_TITLE

        try:
            if " (@" in text:
                title = text.split(" (@")[0].strip()
            elif re.search(r" - [0-9]*\s", text):
                title = text.split(" - ")[0].strip()
        except IndexError:
            logger.error(f"Failed to extract title from '{text}'")
            print(f"ERROR: Failed to extract title from '{text}'")

        if title == DEFAULT_ALBUM_TITLE:
            title = self._get_article_title(soup)

        logger.info(f"Extracted title: {title}")
        return title

    async def _extract_paginated_images(
        self,
        owner_id: str,
        album_id: str,
        pagination_size: int = DEFAULT_PAGINATION_SIZE,
    ) -> list[str]:
        """
        Asynchronously retrieves all image URLs from a paginated album using
        the site's API.

        Args:
            owner_id (str): The owner ID of the album.
            album_id (str): The album ID to fetch images from.
            pagination_size (int): Number of images to fetch per request. Defaults to
                DEFAULT_PAGINATION_SIZE.

        Returns:
            list[str]: A list of image URLs extracted from all pages of the
                album.
        """
        logger.debug(
            f"Extracting paginated images for owner_id: {owner_id}, album_id: {album_id}"
        )

        images: list[str] = []
        url: str = self.site_url + "/cms/load-more-photos.php"

        payload: dict[str, str | int] = {
            "album_id": album_id,
            "owner_id": owner_id,
            "download": 1,
            "download_id": 0,
            "offset": 0,
            "limit": pagination_size,
        }

        while True:
            try:
                response = await self.session.post(
                    url, json=payload, timeout=MAX_TIMEOUT
                )
                response.raise_for_status()
                response_json: dict[str, Any] = await response.json()
            except Exception as e:
                logger.error(f"Failed to fetch paginated images: {e}")
                print(f"ERROR: Failed to fetch paginated images: {e}")
                break
            photos: list[dict[str, str]] = response_json["photos"]
            if not photos:
                break

            logger.info(f"Fetched {len(photos)} photos from offset {payload['offset']}")
            for photo in photos:
                soup = BeautifulSoup(photo["html"], "html.parser")
                anchor: Tag | NavigableString | None = soup.find(
                    "a", href=lambda href: self.base_media_url in href
                )
                if not anchor or not isinstance(anchor, Tag):
                    continue
                href: str | list[str] | None = anchor.get("href")
                if not href:
                    continue
                if isinstance(href, list):
                    href = href[0]
                logger.debug(f"Found image URL: {href}")
                images.append(href)

            if len(photos) < pagination_size:
                break

            payload["offset"] += pagination_size

        return images

    def _extract_album_info(self, soup: BeautifulSoup) -> tuple[str, str]:
        """
        Extracts the owner ID and album ID from the provided BeautifulSoup
        object.

        Attempts to locate these IDs by first searching for a preload link tag
        with rel="preload" and as="image", extracting the relevant path
        segments from its href. If not found, it falls back to parsing the
        content of the og:image meta tag. Returns empty strings if neither
        method yields valid IDs.

        Args:
            soup (BeautifulSoup): Parsed HTML content of the album page.

        Returns:
            tuple[str, str]: A tuple containing the owner ID and album ID, or
            empty strings if not found.
        """
        logger.debug("Extracting album info from soup")

        preload: Tag | NavigableString | None = soup.find(
            "link", {"rel": "preload", "as": "image"}
        )
        if preload and isinstance(preload, Tag):
            href: str | list[str] = preload.get("href", "")
            if isinstance(href, list):
                href = href[0]
            if href:
                parts: list[str] = href.split("/")[-3:-1]
                owner_id, album_id = parts[0], parts[1]
                logger.info(
                    f"Extracted album info from preload: owner_id={owner_id}, album_id={album_id}"
                )
                return owner_id, album_id

        og_image: Tag | NavigableString | None = soup.find(
            "meta", {"property": "og:image"}
        )
        if og_image and isinstance(og_image, Tag):
            content: str | list[str] = og_image.get("content", "")
            if isinstance(content, list):
                content = content[0]
            if content:
                parts = content.split("/")
                owner_id, album_id = parts[-2], parts[-1].split(".")[0]
                logger.info(
                    f"Extracted album info from og:image: owner_id={owner_id}, album_id={album_id}"
                )
                return owner_id, album_id

        logger.error("Failed to extract album info from soup")
        return "", ""

    async def extract_media(self, soup: BeautifulSoup) -> list[str]:
        """
        Asynchronously extracts all media (image) URLs from an album or page.

        If pagination is enabled, retrieves images using paginated API requests
        based on album and owner IDs extracted from the page. Otherwise,
        collects image URLs from anchor tags referencing the base media URL,
        or, if none are found, from links starting with "https://sun". Cleans
        and normalizes URLs as needed.

        Args:
            soup (BeautifulSoup): Parsed HTML content of the album or page.

        Returns:
            list[str]: List of extracted image URLs.
        """
        logger.debug("Extracting media from soup")

        if self.pagination:
            owner_id, album_id = self._extract_album_info(soup)
            if not owner_id or not album_id:
                logger.error("Failed to find album information in the page.")
                print("ERROR: Failed to find album information in the page.")
                return []

            return await self._extract_paginated_images(owner_id, album_id)

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
        for tag in soup.find_all(
            "a", href=lambda href: href and href.startswith("https://sun")  # type: ignore
        ):
            href: str = tag.get("href")
            logger.info(f"Found sun9 image before cleanup: {href}")
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
        model_url: str,
        album_fetcher: Callable[[str], Awaitable[list[str]]],
        title_extractor: Callable[[BeautifulSoup], str],
    ) -> AsyncGenerator[tuple[list[str], str], None]:
        """
        Asynchronously iterates through paginated model pages to yield album
        URLs and the model name.

        Args:
            model_url (str): The URL of the model page to start from.
            album_fetcher (Callable): A function that fetches album URLs from a
                page.
            title_extractor (Callable): A function that extracts the model name
                from the page.

        Yields:
            Tuples containing a list of album URLs and the model name for each
            page with albums found.
        """
        logger.debug(f"Finding model albums for URL: {model_url}")

        # Clean the URL removing the query parameters
        model_url = model_url.split("?")[0]

        soup: BeautifulSoup | None = await self.fetch_soup(model_url)
        if not soup:
            logger.error(f"Failed to fetch or parse model page: {model_url}")
            return

        model_name: str = title_extractor(soup)
        i = 1
        albums_found = True

        while albums_found:
            page_url: str = f"{model_url}?page={i}"
            logger.debug("Fetching albums from page %s", page_url)
            albums_extracted: list[str] = await album_fetcher(page_url)
            if not albums_extracted:
                albums_found = False
                continue

            logger.info(f"Found {len(albums_extracted)} albums on page {page_url}")
            yield albums_extracted, model_name
            i += 1

            # Sleep for a while to avoid being banned
            await asyncio.sleep(1)

        logger.debug(f"Finished finding albums for model: {model_name}")

    @override
    async def download(self, url: str) -> list[dict[str, str]]:
        """
        Download and extract media and metadata from a given album or model
        URL.

        If the URL corresponds to an album, processes and returns its media and
        metadata. If the URL matches a model or cosplay section, finds all
        associated albums and processes them concurrently, aggregating their
        results. Returns an empty list for unknown URL formats.

        Args:
            url (str): The album, model, or cosplay URL to process.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing media URLs
            and associated metadata.
        """
        logger.debug(f"Downloading from URL {url} using {self.__class__.__name__}")

        if url.startswith(self.site_url + self.album_path):
            logger.info(f"Downloading album from {url}")
            return await self.process_album(url, self.extract_media, self.extract_title)
        elif (
            (self.model_url and url.startswith(self.model_url))
            or (self.cosplay_url and url.startswith(self.cosplay_url))
            or (self.fandom_url and url.startswith(self.fandom_url))
        ):
            logger.info(f"Downloading albums for model or cosplay from {url}")
            results: list[dict[str, str]] = []

            # Find all the albums for the model incrementally
            async for albums, _ in self._find_model_albums(
                url, self.fetch_page_albums, self.extract_title
            ):
                logger.info(f"Processing {len(albums)} albums concurrently")
                tasks: list[CoroutineType[Any, Any, list[dict[str, str]]]] = [
                    self.process_album(album, self.extract_media, self.extract_title)
                    for album in albums
                ]

                # Process the tasks for this chunk and collect results
                chunk_results: list[dict[str, str]] = list(
                    chain.from_iterable(await asyncio.gather(*tasks))
                )
                results.extend(chunk_results)

            return results

        logger.error(f"Unknown URL format: {url}")
        print(f"ERROR: Unknown URL format: {url}")
        return []
