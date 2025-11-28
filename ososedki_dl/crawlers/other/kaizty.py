"""Downloader for https://www.kaizty.com"""

from __future__ import annotations

from .cosxuxi_club import CosxuxiClubCrawler


class KaiztyCrawler(CosxuxiClubCrawler):
    site_url = "https://www.kaizty.com"
    site_name = "Kaizty Photos"
    title_separator = " | "
