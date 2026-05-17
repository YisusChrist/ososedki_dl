"""Downloader for https://husvjjal.blogspot.com"""

from __future__ import annotations

import asyncio
import json
from collections import deque
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString
from rich import print
from typing_extensions import override

from ..base_crawler import BaseCrawler

if TYPE_CHECKING:
    from typing import Any

    from bs4.element import BeautifulSoup, Tag


class HusvjjalBlogspotCrawler(BaseCrawler):
    site_url = "https://husvjjal.blogspot.com"

    async def get_related_albums(self, album_url: str) -> list[str]:
        """
        Fetches related album URLs for a given album by querying the site's
        JSON feed endpoint.

        Args:
            album_url (str): The URL of the album for which to find related
                albums.

        Returns:
            list[str]: A list of related album URLs extracted from the feed.
        """
        print(f"Fetching related albums for {album_url}")

        headers: dict[str, str] = {"Referer": album_url}
        js_url: str = f"{self.site_url}/feeds/posts/default"
        params: dict[str, str] = {
            "alt": "json-in-script",
            "callback": "BloggerJS.related",
            "max-results": "12",
            "q": 'label:"Video"',
        }

        js_script: str = await self.downloader.fetch(
            js_url, headers=headers, params=params
        )
        script_json: str = (
            js_script.split("BloggerJS.related(")[1].split(");")[0].strip()
        )
        # Convert the str to a dictionary
        js_dict: dict[str, Any] = json.loads(script_json)

        js_feed_entry: list[dict[str, list[dict[str, str]]]] = js_dict["feed"]["entry"]

        related_albums: list[str] = []
        for entry in js_feed_entry:
            entry_link: list[dict[str, str]] = entry["link"]
            for link in entry_link:
                if link["rel"] == "alternate" and link["type"] == "text/html":
                    related_albums.append(link["href"])
                    break

        return related_albums

    def get_max_stream(self, js_script: str | None) -> dict[str, str]:
        """
        Extracts the video stream with the highest format ID from a JavaScript
        VIDEO_CONFIG snippet.

        Args:
            js_script (str): JavaScript code containing a VIDEO_CONFIG variable
                assignment.

        Returns:
            dict[str, str]: The stream dictionary with the highest format ID,
            or an empty dictionary if not found.
        """
        if not js_script:
            print("No js_script found")
            return {}

        video_config_str: str = (
            js_script.split("var VIDEO_CONFIG = ")[1].split(";")[0].strip()
        )
        # Convert the video config to a dictionary
        video_config: dict[str, Any] = json.loads(video_config_str)

        # Find the one with the highest format_id
        max_stream: dict[str, str] = max(
            video_config["streams"], key=lambda x: x["format_id"]
        )
        if not max_stream:
            print("No max stream found")
            return {}

        return max_stream

    @override
    def get_album_title(self, soup: BeautifulSoup) -> str:
        # Title is hardcoded to "husvjjal" in download(), so this is a fallback
        return "husvjjal"

    async def process_image(self, img: str) -> str | None:
        img_hostname: str | None = urlparse(img).hostname
        if img_hostname and img_hostname == "i.postimg.cc":
            return img

        soup: BeautifulSoup = await self.fetch_soup(img)

        download_link: Tag | NavigableString | None = soup.find(
            "a",
            {"id": "download"},
        )
        if not download_link or isinstance(download_link, NavigableString):
            return

        download_href: str | list[str] = download_link.get("href", "")
        if isinstance(download_href, list):
            download_href = download_href[0]

        download_href = download_href.strip()
        download_hostname: str | None = urlparse(download_href).hostname
        if download_hostname and download_href.startswith("https://"):
            return download_href

    async def process_video(self, vid: str) -> str | None:
        soup: BeautifulSoup = await self.fetch_soup(vid)

        js_script: Tag | NavigableString | None = soup.find(
            "script",
            {"type": "text/javascript"},
        )
        if not js_script or isinstance(js_script, NavigableString):
            return

        max_stream: dict[str, str] = self.get_max_stream(js_script.string)

        play_url: str = max_stream.get("play_url", "").strip()
        play_hostname: str | None = urlparse(play_url).hostname
        if play_hostname and play_url.startswith("https://"):
            return play_url
        return None

    def find_image_url(self, tag: Tag) -> str | None:
        """
        Extracts image URL from an anchor tag that may contain an image,
        checking against allowed hostnames.

        Args:
            img (str): The URL of the image to check.

        Returns:
            str | None: The validated image URL or None if not found.
        """
        allowed_img_hostnames: set[str] = {"i.postimg.cc", "postimg.cc"}

        img_tag: Tag | NavigableString | None = tag.find("img")
        if not img_tag or isinstance(img_tag, NavigableString):
            return

        href: str = tag.get("href", "").strip()
        src: str = img_tag.get("src", "").strip()

        # Parse the URL to check the hostname
        href_hostname: str | None = urlparse(href).hostname
        src_hostname: str | None = urlparse(src).hostname

        if href_hostname and href_hostname in allowed_img_hostnames:
            return href
        elif src_hostname and src_hostname in allowed_img_hostnames:
            return src

    @override
    async def get_media_urls(self, soup: BeautifulSoup) -> list[str]:
        """
        Asynchronously extracts downloadable image and video URLs from a
        BeautifulSoup-parsed album page.

        Scans anchor tags for images hosted on allowed domains and resolves
        indirect image links by fetching their download pages. Identifies
        embedded video iframes, fetches their pages, and extracts the highest
        quality video stream URL. Returns a list of validated HTTPS URLs for
        all found media.

        Args:
            soup (BeautifulSoup): Parsed HTML content of the album page.

        Returns:
            list[str]: List of HTTPS URLs pointing to downloadable images and
            videos found on the album page.
        """
        images: list[str | None] = [
            self.find_image_url(tag) for tag in soup.find_all("a")
        ]
        videos: list[str] = [
            tag.get("src", "").strip()
            for tag in soup.find_all("iframe", class_="b-hbp-video b-uploaded")
        ]

        tasks = [self.process_image(img) for img in images if img] + [
            self.process_video(vid) for vid in videos
        ]
        results = await asyncio.gather(*tasks)
        # Filter out the empty strings and None values
        return [url for url in results if url and url.startswith("https://")]

    @override
    async def download(self, url: str) -> list[dict[str, str]]:
        """
        Download all media items from a given Husvjjal Blogspot URL, including
        related albums.

        If the URL points to a single album, downloads its media and
        recursively processes related albums. If the URL is a profile or index
        page, finds all album links, downloads their media, and also processes
        related albums not already included. Returns a combined list of media
        dictionaries from all processed albums.

        Args:
            url (str): The album, profile, or index page URL to process.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing media
            information from all discovered albums.
        """
        profile_url: str = url.rstrip("/")
        if profile_url.endswith(".html"):
            results: list[dict[str, str]] = await self.process_album(
                profile_url, title="husvjjal"
            )
            related_albums: list[str] = await self.get_related_albums(profile_url)
            for related_album in related_albums:
                results += await self.process_album(related_album, title="husvjjal")
            return results

        soup: BeautifulSoup = await self.fetch_soup(profile_url)

        album_classes: list[str] = [
            "card-image ratio o-hidden mask ratio-16:9",
            "gallery-name fw-500 font-primary fs-5 l:fs-3",
            "gallery ratio mask carousel-cell gallery-default ratio-4:3",
            "gallery ratio mask carousel-top gallery-featured ratio-16:9",
        ]

        albums_html: list[Tag] = soup.find_all("a", class_=album_classes)
        albums: list[str] = list({album["href"] for album in albums_html})

        results: list[dict[str, str]] = []
        # Turn your initial list into a queue
        queue: deque[str] = deque(albums)
        # Track visited albums to prevent infinite loops if Site A links to Site B, and B links to A
        visited: set[str] = set(albums)

        while queue:
            # Pop the oldest item from the left side of the queue (FIFO)
            album_url: str = queue.popleft()

            results += await self.process_album(album_url, title="husvjjal")
            related_albums: list[str] = await self.get_related_albums(album_url)

            for related_album in related_albums:
                if related_album not in visited:
                    visited.add(related_album)
                    queue.append(related_album)

        return results
