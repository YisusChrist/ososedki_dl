"""Downloader for https://sorrymother.top"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from ...consts import DEFAULT_ALBUM_TITLE
from ..base_crawler import BaseCrawler

if TYPE_CHECKING:
    from bs4 import BeautifulSoup


class SorryMotherCrawler(BaseCrawler):
    site_url = "https://sorrymother.top"
    base_url: str = "https://pics.sorrymother.video/"
    headers = {"Referer": site_url, "Range": "bytes=0-"}

    @override
    def get_album_title(self, soup: BeautifulSoup, url: str) -> str:
        """
        Extracts the content title from the HTML soup by locating the first <a>
        tag with class "entry-tag".

        Args:
            soup (BeautifulSoup): The parsed HTML content of the page.
            url (str): The URL of the page being processed (not used in this
                method).

        Returns:
            str: The text of the first matching tag, or `DEFAULT_ALBUM_TITLE`
                if no such tag is found.
        """
        # TODO: Add a better way to get the title, this fails if there is no tag
        # or if the first tag is not the correct title
        tags = soup.find_all("a", class_="entry-tag")
        return tags[0].text if tags else DEFAULT_ALBUM_TITLE

    @override
    async def get_media_urls(self, soup: BeautifulSoup, url: str) -> list[str]:
        """
        Extracts and normalizes media URLs from the provided HTML soup.

        Finds all image and video sources relevant to the site, removes
        resolution suffixes from image filenames, and strips query parameters
        from video URLs.

        Args:
            soup (BeautifulSoup): The parsed HTML content to search for media
                elements.
            url (str): The URL of the page being processed (not used in this
                method).

        Returns:
            list[str]: List of cleaned image and video URLs found in the soup.
        """
        images_list: list[str] = [
            img["src"] for img in soup.find_all("img") if self.base_url in img["src"]
        ]
        # Remove the resolution from the image name
        images: list[str] = []
        for image in images_list:
            parts: list[str] = image.split("-")
            new_name: str = "-".join(parts[:-1]) + "." + parts[-1].split(".")[-1]
            images.append(new_name)
        videos: list[str] = [
            video["data-src"].strip()
            for video in soup.find_all("button", class_="cfp_dl")
        ]
        return images + videos
