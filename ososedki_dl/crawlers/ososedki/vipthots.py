"""Downloader for https://vipthots.com"""

from ..base_crawler import BaseCrawler


class VipThotsCrawler(BaseCrawler):
    site_url = "https://vipthots.com"
    base_image_path = "/images/a/"
    album_path = "/p/"
    model_url = None
    cosplay_url = None
    button_class = None
