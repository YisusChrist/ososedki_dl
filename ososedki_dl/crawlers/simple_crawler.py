from abc import ABC, abstractmethod

from ._common import CrawlerContext


class SimpleCrawler(ABC):
    site_url: str

    @abstractmethod
    async def download(self, context: CrawlerContext, url: str) -> list[dict[str, str]]:
        raise NotImplementedError("Each crawler must implement its own download method")
