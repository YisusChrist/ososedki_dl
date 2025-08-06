"""Downloader for https://waifubitches.com"""

from ..ososedki_crawler import OsosedkiBaseCrawler


class WaifuBitchesCrawler(OsosedkiBaseCrawler):
    site_url = "https://waifubitches.com"
    base_image_path = "/images/a/"
    album_path = "/gallery/"
    model_url = f"{site_url}/model/"
    cosplay_url = f"{site_url}/cosplay/"
    fandom_url = f"{site_url}/fandom/"
    button_class = "btn btn-sm bg-pink-pink"
    pagination = True
