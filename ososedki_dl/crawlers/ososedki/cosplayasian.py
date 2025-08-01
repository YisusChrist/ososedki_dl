"""Downloader for https://cosplayasian.com"""

from ososedki_dl.crawlers.base_crawler import BaseCrawler


class CosplayAsianCrawler(BaseCrawler):
    site_url = "https://cosplayasian.com"
    base_image_path = "/images/a/"
    album_path = "/post/"
    model_url = None
    cosplay_url = f"{site_url}/cos/"
    button_class = None
