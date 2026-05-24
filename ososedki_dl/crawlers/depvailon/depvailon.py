"""Downloader for https://www.depvailon.com"""

from __future__ import annotations

from .cosxuxi_club import CosxuxiClubCrawler


class DepvailonCrawler(CosxuxiClubCrawler):
    site_url = "https://www.depvailon.com"
    site_name = "Depvailon.Com"
    title_separator = " | "
