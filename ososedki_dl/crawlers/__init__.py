from __future__ import annotations

from typing import Type, Union

from ._common import CrawlerContext
from .base_crawler import BaseCrawler
from .ososedki import crawlers as ososedki_crawlers
from .other import crawlers as other_crawlers
from .simple_crawler import SimpleCrawler

CrawlerType = Union[Type[BaseCrawler], Type[SimpleCrawler]]
CrawlerInstance = Union[BaseCrawler, SimpleCrawler]
crawlers: list[CrawlerType] = ososedki_crawlers + other_crawlers

__all__: list[str] = [
    "CrawlerContext",
    "BaseCrawler",
    "SimpleCrawler",
    "crawlers",
    "CrawlerInstance",
]
