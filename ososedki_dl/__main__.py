"""Main module for the package."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aiohttp import ClientSession
from aiohttp_client_cache.session import CachedSession
from core_helpers.utils import print_welcome
from rich import print
from rich.traceback import install

from .cli import get_parsed_args, handle_config_command
from .config import configure_paths
from .consts import (CACHE_PATH, CONFIG_FILE, CONFIG_PATH, EXIT_SUCCESS,
                     GITHUB, LOG_FILE, LOG_PATH, PACKAGE)
from .consts import __desc__ as DESC
from .consts import __version__ as VERSION
from .crawlers import crawlers as crawler_modules
from .download import get_user_agent
from .logs import logger
from .scrapper import generic_download
from .utils import exit_session, get_user_input

if TYPE_CHECKING:
    from argparse import Namespace
    from pathlib import Path


async def run_main_loop(dest_path: Path, cache: bool) -> None:
    SessionType = CachedSession if cache else ClientSession
    session_type_name = "cached" if cache else "non-cached"
    msg = f"Using {session_type_name} session for downloads."
    print(msg)
    logger.info(msg)

    headers: dict[str, str] = {"User-Agent": get_user_agent()}
    async with SessionType(headers=headers) as session:
        # Dynamically load all crawler modules
        while True:
            urls, download_path = get_user_input(dest_path)

            await generic_download(
                session=session, urls=urls, download_path=download_path
            )


def main() -> None:
    """
    Main function
    """
    args: Namespace = get_parsed_args()
    dest_path: Path = configure_paths(args)

    install()

    CACHE_PATH.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    LOG_PATH.mkdir(parents=True, exist_ok=True)

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

    exit_session(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
