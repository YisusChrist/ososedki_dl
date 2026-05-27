"""Downloader for https://hentaibitches.com"""

from ..ososedki_crawler import OsosedkiBaseCrawler


class HentaiBitchesCrawler(OsosedkiBaseCrawler):
    site_url = "https://hentaibitches.com"
    base_image_path = "/images/posts/"
    album_path = "/p/"
    model_url = f"{site_url}/m/"
    cosplay_url = f"{site_url}" + "{fandom}/{cosplay}/"
    fandom_url = f"{site_url}/f/"
    button_class = None
    title_separator = (
        " free leaked cosplay xxx porn from reddit, onlyfans, fansly, patreon, telegram"
    )
    pagination = False
