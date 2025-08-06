from __future__ import annotations

from typing import Type, Union

from .base_crawler import BaseCrawler, CrawlerContext
from .ososedki import crawlers as ososedki_crawlers
from .ososedki_crawler import OsosedkiBaseCrawler
from .other import crawlers as other_crawlers

CrawlerType = Union[Type[OsosedkiBaseCrawler], Type[BaseCrawler]]
CrawlerInstance = Union[OsosedkiBaseCrawler, BaseCrawler]
crawlers: list[CrawlerType] = ososedki_crawlers + other_crawlers

__all__: list[str] = [
    "BaseCrawler",
    "CrawlerContext",
    "CrawlerInstance",
    "crawlers",
    "OsosedkiBaseCrawler",
]
