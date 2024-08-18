"""Main module for the package."""

import asyncio
from argparse import Namespace

from aiohttp import ClientSession
from rich.traceback import install

from .cli import exit_session, get_parsed_args
from .consts import EXIT_SUCCESS
from .scrapper import generic_download
from .utils import get_user_input


async def run_main_loop() -> None:
    async with ClientSession() as session:
        while True:
            urls, download_path = get_user_input()

            await generic_download(
                session=session, urls=urls, download_path=download_path
            )


def main() -> None:
    """
    Main function
    """
    args: Namespace = get_parsed_args()
    install()

    try:
        asyncio.run(run_main_loop())
    except KeyboardInterrupt:
        pass

    exit_session(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
