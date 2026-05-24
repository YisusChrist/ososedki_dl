"""Downloader for https://lootiu.com"""

from __future__ import annotations

from .cosxuxi_club import CosxuxiClubCrawler


class LootiuCrawler(CosxuxiClubCrawler):
    site_url = "https://lootiu.com"
    site_name = "Lootiu.Com"
    title_separator = " | "
