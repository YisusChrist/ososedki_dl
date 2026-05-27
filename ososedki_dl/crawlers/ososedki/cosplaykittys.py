"""Downloader for https://cosplaykittys.com"""

from ..ososedki_crawler import OsosedkiBaseCrawler


class CosplayKittysCrawler(OsosedkiBaseCrawler):
    site_url = "https://cosplaykittys.com"
    base_image_path = "/images/a/"
    album_path = "/g/"
    model_url = f"{site_url}/m/"
    cosplay_url = f"{site_url}/c/"
    fandom_url = f"{site_url}/f/"
    button_class = None
    pagination = False
