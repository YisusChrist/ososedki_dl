"""Downloader for https://hentailib.net"""

from .hentaibitches import HentaiBitchesCrawler


class HentaiLibCrawler(HentaiBitchesCrawler):
    site_url = "https://hentailib.net"
