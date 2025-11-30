"""Downloader for https://vipthots.com"""

from ..ososedki_crawler import OsosedkiBaseCrawler


class VipThotsCrawler(OsosedkiBaseCrawler):
    site_url = "https://vipthots.com"
    base_image_path = "/images/a/"
    album_path = "/p/"
    model_url = f"{site_url}/m/"
    cosplay_url = f"{site_url}/c/"
    fandom_url = f"{site_url}/f/"
    button_class = "btn btn-sm bg-model"
    pagination = True
