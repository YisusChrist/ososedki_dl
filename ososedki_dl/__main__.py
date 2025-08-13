"""Main module for the package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.traceback import install

from .cli import get_parsed_args
from .commands import run
from .config import load_config
from .consts import CACHE_PATH, CONFIG_PATH, EXIT_SUCCESS, LOG_PATH
from .utils import exit_session

if TYPE_CHECKING:
    from argparse import Namespace
    from pathlib import Path


def main() -> None:
    """
    Main function
    """
    args: Namespace = get_parsed_args()
    dest_path: Path = load_config(args)

    install()

    CACHE_PATH.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    LOG_PATH.mkdir(parents=True, exist_ok=True)

    run(args, dest_path)

    exit_session(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
