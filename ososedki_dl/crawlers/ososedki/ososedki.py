"""Downloader for https://ososedki.com"""

from ..ososedki_crawler import OsosedkiBaseCrawler


class OsosedkiCrawler(OsosedkiBaseCrawler):
    site_url = "https://ososedki.com"
    base_image_path = "/images/a/"
    album_path = "/photos/"
    model_url = None
    cosplay_url = None
    button_class = None
    pagination = False
