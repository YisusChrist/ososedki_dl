"""Downloader for https://cosplaythots.com"""

from ..ososedki_crawler import OsosedkiBaseCrawler


class CosplayThotsCrawler(OsosedkiBaseCrawler):
    site_url = "https://cosplaythots.com"
    base_image_path = "/images/a/"
    album_path = "/p/"
    model_url = None
    cosplay_url = f"{site_url}/c/"
    button_class = None
    pagination = True
