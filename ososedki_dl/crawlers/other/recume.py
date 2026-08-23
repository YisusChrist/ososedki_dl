"""Downloader for https://recu.me"""

from __future__ import annotations

from bs4 import BeautifulSoup
from core_helpers.logs import logger
from rich import print
from typing_extensions import override

from ..base_crawler import BaseCrawler


class RecumeCrawler(BaseCrawler):
    site_url = "https://recu.me"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    }

    video_url: str = site_url + "/performer/{model}/video/{video_id}/play"
    videos_url: str = site_url + "/performer/{model}/latest"
    clips_url: str = site_url + "/clips/{model}/latest"
    kinks_url: str = site_url + "/performer/{model}/kinks/latest"

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
        return self.model

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
        # Handle specific target sections
        if (
            "/kinks/" in url
            or "/clips/" in url
            or ("/performer/" in url and "/latest" in url)
        ):
            return await self.get_urls(soup, url)

        # Default: scrape all endpoints for the performer
        results: list[str] = []
        for endpoint in (self.videos_url, self.clips_url, self.kinks_url):
            formatted_url = endpoint.format(model=self.model)
            results.extend(await self.get_urls(soup, formatted_url))

        return results

    async def get_urls(self, soup: BeautifulSoup, url: str) -> list[str]:
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
        result: list[str] = []
        index = 1

        url = url.rstrip("/")
        url_index: str = url.split("/")[-1]
        if url_index.isdigit() and f"/page/{url_index}" in url:
            index = int(url_index)
            url = url.replace(f"/page/{url_index}", "")

        while True:
            page_url: str = f"{url}/page/{index}"
            print(f"Fetching page {index}: {page_url}")

            response = await self.downloader.fetch(page_url, raw_response=True)
            if response.history and response.history[-1].status == 302:
                print(f"No more pages found for model '{self.model}'. Stopping.")
                break

            html_content = await response.text()
            if not html_content:
                logger.error(f"Failed to fetch {url}: empty HTML content")
                raise ValueError(f"Empty HTML content received from {url}")

            soup = BeautifulSoup(html_content, "html.parser")
            images = soup.find_all(
                "div", class_="video-splash video-splash-loading animate-on-hover"
            )
            if not images:
                print(f"No images found on page {index}. Stopping.")
                break

            result.extend([image.get("data-src") for image in images])

            index += 1

        return result

    @override
    async def download(self, url: str) -> list[dict[str, str]]:
        url = url.rstrip("/")
        if "/kinks/" in url:
            self.model: str = url.split("/kinks/")[0].split("/")[-1]
        elif "/clips/" in url:
            self.model = url.split("/clips/")[1].split("/")[0]
        elif "/video/" in url:
            print(
                "Video downloading is not supported yet. Please use the performer page or clips/kinks pages."
            )
            return []
        elif "/performer/" in url:
            self.model = url.split("/performer/")[1].split("/")[0]
        else:
            logger.error(f"Invalid URL format: {url}")
            raise ValueError(f"Invalid URL format: {url}")

        return await super().download(url)
