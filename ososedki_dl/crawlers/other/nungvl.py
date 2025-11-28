"""Downloader for https://nungvl.net"""

from __future__ import annotations

from .cosxuxi_club import CosxuxiClubCrawler


class NungvlCrawler(CosxuxiClubCrawler):
    site_url = "https://nungvl.net"
    site_name = "NứngVL.net"
    title_separator = " | "
