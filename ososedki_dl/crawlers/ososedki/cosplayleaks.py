"""Downloader for https://cosplayleaks.com"""

from ..ososedki_crawler import OsosedkiBaseCrawler


class CosplayLeaksCrawler(OsosedkiBaseCrawler):
    site_url = "https://cosplayleaks.com"
    base_image_path = "/images/a/"
    album_path = "/photos/"
    model_url = f"{site_url}/model/"
    cosplay_url = f"{site_url}/cosplay/"
    fandom_url = f"{site_url}/fandom/"
    button_class = None
    pagination = True
