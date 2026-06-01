"""Downloader for https://cosxuxi.club"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bs4 import NavigableString
from core_helpers.logs import logger
from typing_extensions import override

from ...consts import DEFAULT_ALBUM_TITLE
from ..base_crawler import BaseCrawler

if TYPE_CHECKING:
    from bs4 import BeautifulSoup, Tag


class CosxuxiClubCrawler(BaseCrawler):
    site_url = "https://cosxuxi.club"
    site_name: str = "CosXuxi Club"
    title_separator: str | None = " - "
    content_div: str = "div.contentme"

    @override
    def get_album_title(self, soup: BeautifulSoup, url: str) -> str:
        """
        Extracts the album title from the page's HTML soup.

        Args:
            soup (BeautifulSoup): The parsed HTML content of the page.
            url (str): The URL of the page being processed (not used in this
                method).

        Returns:
            str: The extracted album title, or a default title if not found.
        """
        if not soup or not soup.title:
            logger.warning(
                f"No title tag found in the soup for {self.__class__.__name__}"
            )
            return DEFAULT_ALBUM_TITLE

        text: str = soup.title.text.strip()
        if f"{self.site_name}: " in text:
            text = text.split(f"{self.site_name}: ")[1].strip()
        if self.title_separator and self.title_separator in text:
            text = text.split(self.title_separator)[0].strip()

        return text or DEFAULT_ALBUM_TITLE

    @override
    async def get_media_urls(self, soup: BeautifulSoup, url: str) -> list[str]:
        """
        Extracts and returns a list of image URLs from the media div that
        contain the specified base URL fragment.

        Args:
            soup (BeautifulSoup): The parsed HTML content of the page.
            url (str): The URL of the page being processed (not used in this
                method).

        Returns:
            list[str]: List of image source URLs matching the base URL filter,
            or an empty list if no valid images are found.
        """
        urls: list[str] = []

        while True:
            # Find all the images inside the div with the specific class
            content_div: Tag | None = soup.select_one(self.content_div)
            if not content_div:
                logger.warning(
                    f"No content div found in the soup for {self.__class__.__name__}"
                )
                break

            page_urls: list[str] = [
                img.get("src") for img in content_div.find_all("img")
            ]
            if not page_urls:
                logger.warning(
                    f"No images found in the content div for {self.__class__.__name__}"
                )
                break

            logger.info(f"Found {len(page_urls)} image(s) on the current page.")
            urls.extend(page_urls)

            # Check if there is a next page
            next_page: Tag | NavigableString | None = soup.find(
                "a", class_="page-numbers", string="Next >"
            )
            if not next_page or isinstance(next_page, NavigableString):
                logger.info("No next page found, ending pagination.")
                break

            next_href: str | list[str] = next_page.get("href", "")
            next_page_url: str = (
                next_href[0] if isinstance(next_href, list) else next_href
            )
            if not next_page_url or not next_page_url.startswith("/"):
                logger.warning(
                    f"Invalid next page URL: {next_page_url}, ending pagination."
                )
                break

            album_url: str = self.site_url + next_page_url
            soup = await self.fetch_soup(album_url)

        return urls
