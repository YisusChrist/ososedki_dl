"""Downloader for https://husvjjal.blogspot.com"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString
from requests import Session
from rich import print
from typing_extensions import override

from ...download import fetch
from .._common import fetch_soup, process_album
from ..simple_crawler import SimpleCrawler

if TYPE_CHECKING:
    from typing import Any

    from aiohttp import ClientSession
    from bs4 import ResultSet
    from bs4.element import Tag
    from requests import Response

    from .._common import CrawlerContext


class HusvjjalBlogspotCrawler(SimpleCrawler):
    site_url = "https://husvjjal.blogspot.com"

    # @lru_cache
    async def download_album(
        self, context: CrawlerContext, album_url: str
    ) -> list[dict[str, str]]:
        return await process_album(
            context=context,
            album_url=album_url,
            title_extractor=lambda _: "husvjjal",
            media_filter=self.husvjjal_blogspot_media_filter,
        )

    async def get_related_albums(
        self, session: ClientSession, album_url: str
    ) -> list[str]:
        print(f"Fetching related albums for {album_url}")

        headers: dict[str, str] = {"Referer": album_url}

        js_url: str = f"{self.site_url}/feeds/posts/default"
        params: dict[str, str] = {
            "alt": "json-in-script",
            "callback": "BloggerJS.related",
            "max-results": "12",
            "q": 'label:"Video"',
        }

        js_script: str = await fetch(
            session=session, url=js_url, headers=headers, params=params
        )
        script_json: str = (
            js_script.split("BloggerJS.related(")[1].split(");")[0].strip()
        )
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

    def get_soup(self, session: Session, url: str) -> BeautifulSoup:
        response: Response = session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def get_max_stream(self, js_script: str) -> dict[str, str]:
        if not js_script:
            print("No js_script found")
            return {}

        video_config_str: str = (
            js_script.split("var VIDEO_CONFIG = ")[1].split(";")[0].strip()
        )
        # Convert the video config to a dictionary
        video_config: dict = json.loads(video_config_str)

        # Find the one with the highest format_id
        max_stream: dict[str, str] = max(
            video_config["streams"], key=lambda x: x["format_id"]
        )
        if not max_stream:
            print("No max stream found")
            return {}

        return max_stream

    def husvjjal_blogspot_media_filter(self, soup: BeautifulSoup) -> list[str]:
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

                soup = self.get_soup(session=session, url=img)
                download_link: Tag | NavigableString | None = soup.find(
                    "a",
                    {"id": "download"},
                )
                if not download_link or isinstance(download_link, NavigableString):
                    continue

                download_href: str | list[str] = download_link.get("href", "")
                if isinstance(download_href, list):
                    download_href = download_href[0]
                download_href = download_href.strip()
                download_hostname: str | None = urlparse(download_href).hostname
                if download_hostname and download_href.startswith("https://"):
                    urls.append(download_href)

            for vid in videos:
                soup = self.get_soup(session=session, url=vid)
                js_script: Tag | NavigableString | None = soup.find(
                    "script",
                    {"type": "text/javascript"},
                )
                if not js_script or isinstance(js_script, NavigableString):
                    continue

                js_script_str: str | None = js_script.string
                if not js_script_str:
                    continue

                max_stream: dict[str, str] = self.get_max_stream(js_script_str)
                if not max_stream:
                    continue

                play_url: str = max_stream.get("play_url", "").strip()
                play_hostname: str | None = urlparse(play_url).hostname
                if play_hostname and play_url.startswith("https://"):
                    urls.append(play_url)

        return urls

    @override
    async def download(self, context: CrawlerContext, url: str) -> list[dict[str, str]]:
        profile_url: str = url
        if profile_url.endswith("/"):
            profile_url = profile_url[:-1]

        if profile_url.endswith(".html"):
            results: list[dict[str, str]] = await process_album(
                context=context,
                album_url=profile_url,
                title="husvjjal",
                media_filter=self.husvjjal_blogspot_media_filter,
            )
            related_albums: list[str] = await self.get_related_albums(
                context.session,
                profile_url,
            )
            for related_album in related_albums:
                results += await process_album(
                    context=context,
                    album_url=related_album,
                    title="husvjjal",
                    media_filter=self.husvjjal_blogspot_media_filter,
                )
            return results

        soup: BeautifulSoup | None = await fetch_soup(context.session, profile_url)
        if not soup:
            return []

        album_classes: list[str] = [
            "card-image ratio o-hidden mask ratio-16:9",
            "gallery-name fw-500 font-primary fs-5 l:fs-3",
            "gallery ratio mask carousel-cell gallery-default ratio-4:3",
            "gallery ratio mask carousel-top gallery-featured ratio-16:9",
        ]

        albums_html: ResultSet[Any] = soup.find_all("a", class_=album_classes)
        albums: list[str] = list({album["href"] for album in albums_html})

        results = []
        index = 0
        while index < len(albums):
            album: str = albums[index]
            results += await self.download_album(context, album)
            related_albums = await self.get_related_albums(context.session, album)
            for related_album in related_albums:
                if related_album not in albums:
                    albums.append(related_album)

            index += 1  # Move to the next album in the list

        return results
