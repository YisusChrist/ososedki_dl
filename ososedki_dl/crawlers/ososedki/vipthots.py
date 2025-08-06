"""Downloader for https://vipthots.com"""

from ..ososedki_crawler import OsosedkiBaseCrawler


class VipThotsCrawler(OsosedkiBaseCrawler):
    site_url = "https://vipthots.com"
    base_image_path = "/images/a/"
    album_path = "/p/"
    model_url = None
    cosplay_url = None
    button_class = None
    pagination = True
