from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._common import CrawlerContext


class SimpleCrawler(ABC):
    site_url: str
    context: CrawlerContext

    def __init__(self, context: CrawlerContext) -> None:
        self.context = context

    @abstractmethod
    async def download(self, url: str) -> list[dict[str, str]]:
        raise NotImplementedError("Each crawler must implement its own download method")
