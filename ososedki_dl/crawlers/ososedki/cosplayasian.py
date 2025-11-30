"""Downloader for https://cosplayasian.com"""

from ..ososedki_crawler import OsosedkiBaseCrawler


class CosplayAsianCrawler(OsosedkiBaseCrawler):
    site_url = "https://cosplayasian.com"
    base_image_path = "/images/a/"
    album_path = "/post/"
    model_url = f"{site_url}/mod/"
    cosplay_url = f"{site_url}/cos/"
    fandom_url = f"{site_url}/fan/"
    button_class = None
    pagination = True
