"""Downloader for https://sorrymother.to"""

from typing import override

from bs4 import BeautifulSoup

from ososedki_dl.crawlers._common import CrawlerContext, process_album
from ososedki_dl.crawlers.simple_crawler import SimpleCrawler


class SorryMotherCrawler(SimpleCrawler):
    site_url = "https://sorrymother.to"
    base_url: str = "https://pics.sorrymother.video/"

    def sorrymother_title_extractor(self, soup: BeautifulSoup) -> str:
        # TODO: Add a better way to get the title, this fails if there is no tag
        # or if the first tag is not the correct title
        tags = soup.find_all("a", class_="entry-tag")
        return tags[0].text if tags else "Untitled"

    def sorrymother_media_filter(self, soup: BeautifulSoup) -> list[str]:
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
            video["src"].split("?")[0]
            for video in soup.find_all("source", {"type": "video/mp4"})
        ]
        return images + videos

    @override
    async def download(self, context: CrawlerContext, url: str) -> list[dict[str, str]]:
        return await process_album(
            context,
            url,
            self.sorrymother_media_filter,
            self.sorrymother_title_extractor,
        )
