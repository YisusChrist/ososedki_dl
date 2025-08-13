# commands.py
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aiohttp import ClientSession
from aiohttp_client_cache.session import CachedSession
from core_helpers.utils import print_welcome
from fake_useragent import UserAgent
from rich import print

from .cli import handle_config_command
from .consts import (CONFIG_FILE, GITHUB, LOG_FILE, MIN_USER_AGENT_VERSION,
                     PACKAGE)
from .consts import __desc__ as DESC
from .consts import __version__ as VERSION
from .crawlers import crawlers as crawler_modules
from .logs import logger
from .scrapper import generic_download
from .utils import get_user_input

if TYPE_CHECKING:
    from argparse import Namespace
    from pathlib import Path



async def run_main_loop(dest_path: Path, cache: bool) -> None:
    """
    Run the main loop for downloading media.

    Args:
        dest_path (Path): Destination path for downloads.
        cache (bool): Whether to use a cached session.
    """
    SessionType = CachedSession if cache else ClientSession
    session_type_name = "cached" if cache else "non-cached"
    msg = f"Using {session_type_name} session for downloads."
    print(msg)
    logger.info(msg)

    ua = UserAgent(min_version=MIN_USER_AGENT_VERSION)
    headers: dict[str, str] = {"User-Agent": ua.random}
    async with SessionType(headers=headers) as session:
        # Dynamically load all crawler modules
        while True:
            urls, download_path = get_user_input(dest_path)

            await generic_download(
                session=session, urls=urls, download_path=download_path
            )


def run(args: Namespace, dest_path: Path) -> None:
    """
    Run a command if a matching CLI flag is found.

    Args:
        args (Namespace): Parsed command line arguments.
        dest_path (Path): Destination path for downloads.
    """
    if args.config_dir:
        print(CONFIG_FILE)
    elif args.log_dir:
        print(LOG_FILE)
    elif args.print_config is not None:
        handle_config_command(args)
    elif args.list_supported_sites:
        urls: list[str] = sorted(crawler.site_url for crawler in crawler_modules)
        for url in urls:
            print(url)
    else:
        print_welcome(PACKAGE, VERSION, DESC, GITHUB)
        try:
            asyncio.run(run_main_loop(dest_path, args.cache))
        except KeyboardInterrupt:
            pass
