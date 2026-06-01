"""Downloader for https://thismore.fun"""

from __future__ import annotations

from .cosxuxi_club import CosxuxiClubCrawler


class ThisMoreFunCrawler(CosxuxiClubCrawler):
    site_url = "https://thismore.fun"
    site_name = "ThisMore.Fun"
    title_separator = " | "
    content_div = "div.desc.contentme"
