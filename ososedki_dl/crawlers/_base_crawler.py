from pathlib import Path

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from rich.progress import Progress, TaskID

from ososedki_dl.crawlers._common import (fetch_soup, process_model_album,
                                          search_ososedki_media,
                                          search_ososedki_title)


class BaseCrawler:
    def __init__(
        self,
        download_url: str,
        base_url: str,
        model_url: str | None,
        cosplay_url: str | None,
        album_path_pattern: str,
    ) -> None:
        self.download_url: str = download_url
        self.base_url: str = base_url
        self.model_url: str | None = model_url
        self.cosplay_url: str | None = cosplay_url
        self.album_path_pattern: str = album_path_pattern

    def title_extractor(
        self, soup: BeautifulSoup, button_class: str | None = None
    ) -> str:
        return search_ososedki_title(soup=soup, button_class=button_class)

    def media_filter(self, soup: BeautifulSoup) -> list[str]:
        return search_ososedki_media(soup=soup, base_url=self.base_url)

    async def fetch_page_albums(
        self, session: ClientSession, page_url: str
    ) -> list[str]:
        soup: BeautifulSoup | None = await fetch_soup(session, page_url)
        if not soup:
            return []

        albums: list[str] = [
            f"{self.download_url}{a['href']}"
            for a in soup.find_all(
                "a", href=lambda x: x and x.startswith(self.album_path_pattern)
            )
        ]
        return list(set(albums))

    async def download_album(
        self,
        session: ClientSession,
        album_url: str,
        download_path: Path,
        progress: Progress,
        task: TaskID,
    ) -> list[dict[str, str]]:
        return await process_model_album(
            session=session,
            album_url=album_url,
            model_url=self.model_url,
            cosplay_url=self.cosplay_url,
            download_path=download_path,
            progress=progress,
            task=task,
            album_fetcher=self.fetch_page_albums,
            title_extractor=self.title_extractor,
            media_filter=self.media_filter,
        )
