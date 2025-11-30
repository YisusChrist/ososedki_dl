"""Downloader for https://cosplayboobs.com"""

from ..ososedki_crawler import OsosedkiBaseCrawler


class CosplayBoobsCrawler(OsosedkiBaseCrawler):
    site_url = "https://cosplayboobs.com"
    base_image_path = "/images/a/"
    album_path = "/album/"
    model_url = f"{site_url}/model/"
    cosplay_url = f"{site_url}/cosplay/"
    fandom_url = f"{site_url}/fandom/"
    button_class = "btn btn-sm bg-model"
    pagination = True
