from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._common import CrawlerContext


class SimpleCrawler(ABC):
    site_url: str
    context: CrawlerContext

    def __init__(self, context: CrawlerContext) -> None:
        """
        Initialize the SimpleCrawler with a given crawling context.

        Args:
            context (CrawlerContext): The context containing configuration and
                state for the crawler instance.
        """
        self.context = context

    @abstractmethod
    async def download(self, url: str) -> list[dict[str, str]]:
        """
        Asynchronously downloads and parses content from the specified URL.

        Args:
            url (str): The URL to crawl and extract data from.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing extracted
            data.

        Raises:
            NotImplementedError: If the method is not implemented by a
                subclass.
        """
        raise NotImplementedError("Each crawler must implement its own download method")
