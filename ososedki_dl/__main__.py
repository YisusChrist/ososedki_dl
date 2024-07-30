import asyncio
from argparse import Namespace

from aiohttp import ClientSession
from rich.traceback import install

from .cli import exit_session, get_parsed_args
from .consts import EXIT_SUCCESS
from .scrapper import downloaders, generic_download
from .utils import get_user_input


async def run_main_loop() -> None:
    async with ClientSession() as session:
        while True:
            url, download_path = get_user_input()

            # Find the appropriate downloader based on the URL
            for domain, downloader in downloaders.items():
                if url.startswith(domain):
                    await generic_download(
                        session=session,
                        urls=[url],
                        download_path=download_path,
                        download_func=downloader,
                    )
                    break
            else:
                print(f"No downloader found for URL: {url}")


def main() -> None:
    """
    Main function
    """
    args: Namespace = get_parsed_args()
    install()

    run = True
    while run:
        try:
            asyncio.run(run_main_loop())
        except KeyboardInterrupt:
            run = False

    exit_session(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
