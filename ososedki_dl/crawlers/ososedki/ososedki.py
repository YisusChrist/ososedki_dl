"""Downloader for https://ososedki.com"""

from ..base_crawler import BaseCrawler


class OsosedkiCrawler(BaseCrawler):
    site_url = "https://ososedki.com"
    base_image_path = "/images/a/"
    album_path = "/photos/"
    model_url = None
    cosplay_url = None
    button_class = None
    pagination = False
