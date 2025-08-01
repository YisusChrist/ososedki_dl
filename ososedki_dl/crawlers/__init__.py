from ososedki_dl.crawlers.base_crawler import BaseCrawler
from ososedki_dl.crawlers.ososedki import crawlers as ososedki_crawlers
from ososedki_dl.crawlers.other import crawlers as other_crawlers
from ososedki_dl.crawlers.simple_crawler import SimpleCrawler

CrawlerType = BaseCrawler | SimpleCrawler
crawlers: list[CrawlerType] = ososedki_crawlers + other_crawlers
