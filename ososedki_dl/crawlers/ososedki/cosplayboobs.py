"""Downloader for https://cosplayboobs.com"""

from ososedki_dl.crawlers.base_crawler import BaseCrawler


class CosplayBoobsCrawler(BaseCrawler):
    site_url = "https://cosplayboobs.com"
    base_image_path = "/images/a/"
    album_path = "/album/"
    model_url = f"{site_url}/model/"
    cosplay_url = f"{site_url}/cosplay/"
    button_class = "btn btn-sm bg-model"
