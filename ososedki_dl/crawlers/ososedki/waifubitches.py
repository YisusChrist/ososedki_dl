"""Downloader for https://waifubitches.com"""

from ososedki_dl.crawlers.base_crawler import BaseCrawler


class WaifuBitchesCrawler(BaseCrawler):
    site_url = "https://waifubitches.com"
    base_image_path = "/images/a/"
    album_path = "/gallery/"
    model_url = f"{site_url}/model/"
    cosplay_url = f"{site_url}/cosplay/"
    button_class = "btn btn-sm bg-pink-pink"
