"""Main module for the package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from core_helpers import logger
from rich.traceback import install

from .cli import get_parsed_args
from .commands import run
from .config import load_config
from .consts import (CACHE_PATH, CONFIG_PATH, EXIT_SUCCESS, LOG_FILE, LOG_PATH,
                     PACKAGE)
from .utils import exit_session

if TYPE_CHECKING:
    from argparse import Namespace


def main() -> None:
    """
    Main function
    """
    args: Namespace = get_parsed_args()
    logger.setup_logger(PACKAGE, LOG_FILE, args.debug, args.verbose)
    load_config(args)

    install()

    CACHE_PATH.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    LOG_PATH.mkdir(parents=True, exist_ok=True)

    run(args)

    exit_session(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
