from abc import ABC, abstractmethod

from core_helpers.logs import logger

from ._common import CrawlerContext


class SimpleCrawler(ABC):
    site_url: str

    def __init__(self) -> None:
        logger.debug(
            f"Initialized {self.__class__.__name__} with site URL: {self.site_url}"
        )

    @abstractmethod
    async def download(self, context: CrawlerContext, url: str) -> list[dict[str, str]]:
        raise NotImplementedError("Each crawler must implement its own download method")
