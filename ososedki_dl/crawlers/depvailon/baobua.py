"""Downloader for https://baobua.net"""

from __future__ import annotations

from .cosxuxi_club import CosxuxiClubCrawler


class BaoBuaCrawler(CosxuxiClubCrawler):
    site_url = "https://baobua.net"
    site_name = "BaoBua.Net"
    title_separator = None
    content_div = "div.article-body"
