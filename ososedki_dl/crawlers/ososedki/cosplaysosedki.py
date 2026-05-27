"""Downloader for https://cosplaysosedki.com"""

from .cosplaykittys import CosplayKittysCrawler


class CosplaySosedkiCrawler(CosplayKittysCrawler):
    site_url = "https://cosplaysosedki.com"
