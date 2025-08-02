"""Downloader for https://ocosplay.com"""

from ..base_crawler import BaseCrawler


class OCosplayCrawler(BaseCrawler):
    site_url = "https://ocosplay.com"
    base_image_path = "/images/a/"
    album_path = "/g/"
    model_url = f"{site_url}/m/"
    cosplay_url = f"{site_url}/c/"
    button_class = "btn btn-sm bg-pink"
