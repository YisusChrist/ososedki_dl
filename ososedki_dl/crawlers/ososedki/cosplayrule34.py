"""Downloader for https://cosplayrule34.com"""

from ..base_crawler import BaseCrawler


class CosplayRule34Crawler(BaseCrawler):
    site_url = "https://cosplayrule34.com"
    base_image_path = "/images/a/"
    album_path = "/post/"
    model_url = f"{site_url}/model/"
    cosplay_url = f"{site_url}/cosplay/"
    button_class = "btn btn-sm bg-pink-pink"
    pagination = True
