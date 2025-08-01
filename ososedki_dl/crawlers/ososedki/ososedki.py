"""Downloader for https://ososedki.com"""

from ososedki_dl.crawlers.base_crawler import BaseCrawler


class OsosedkiCrawler(BaseCrawler):
    site_url = "https://ososedki.com"
    base_image_path = "/images/a/"
    model_url = None
    cosplay_url = None
    button_class = None
