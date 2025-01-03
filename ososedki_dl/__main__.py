"""Main module for the package."""

import asyncio
from argparse import Namespace
from pathlib import Path

from aiohttp import ClientSession
from core_helpers.utils import print_welcome
from rich.traceback import install

from .cli import exit_session, get_parsed_args
from .config import configure_paths
from .consts import EXIT_SUCCESS, GITHUB, PACKAGE
from .consts import __desc__ as DESC
from .consts import __version__ as VERSION
from .scrapper import generic_download, load_crawler_modules
from .utils import get_user_input


async def run_main_loop(dest_path: Path) -> None:
    async with ClientSession() as session:
        # Dynamically load all crawler modules
        load_crawler_modules()
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

    print_welcome(PACKAGE, VERSION, DESC, GITHUB)
    install()

    try:
        asyncio.run(run_main_loop(dest_path))
    except KeyboardInterrupt:
        pass

    exit_session(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
