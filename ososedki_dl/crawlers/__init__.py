from __future__ import annotations

import sys

from .base_crawler import BaseCrawler
from .ososedki import crawlers as ososedki_crawlers
from .ososedki_crawler import OsosedkiBaseCrawler
from .other import crawlers as other_crawlers

if sys.version_info >= (3, 10):
    CrawlerType = type[OsosedkiBaseCrawler] | type[BaseCrawler]
    CrawlerInstance = OsosedkiBaseCrawler | BaseCrawler
    crawlers = ososedki_crawlers + other_crawlers
else:
    from typing import Union

    CrawlerType = Union[type[OsosedkiBaseCrawler], type[BaseCrawler]]
    CrawlerInstance = Union[OsosedkiBaseCrawler, BaseCrawler]
    crawlers = ososedki_crawlers + other_crawlers

__all__: list[str] = [
    "BaseCrawler",
    "CrawlerInstance",
    "crawlers",
    "OsosedkiBaseCrawler",
]
