"""Utility functions for the application."""

import hashlib
import re
import sys
from pathlib import Path
from typing import Any, NoReturn

import aiofiles
import validators  # type: ignore
from rich import print
from rich.prompt import Prompt

from .consts import CACHE_PATH, EXIT_FAILURE, LOG_PATH


def get_valid_url() -> list:
    while True:
        result: list = []
        urls: str = Prompt.ask("Enter the URL to download from")
        url_list = urls.split(" ")
        for u in url_list:
            url = u.strip()
            if validators.url(url):
                result.append(url)
        if result:
            return result
        else:
            print("[bold red]Error:[/] Please enter a valid URL.")


def get_valid_path() -> Path:
    default_path = "downloads"
    while True:
        path: str = Prompt.ask(
            f"Enter the download path",
            default=default_path,
        )
        real_path: Path = Path(path).resolve()
        return real_path


def get_user_input(path: Path) -> tuple[list, Path]:
    print("\n", end="")
    url: list = get_valid_url()
    if not path:
        path = get_valid_path()
    print("\n", end="")

    return url, path


def sanitize_path(path: Path, title: str) -> Path:
    # Define a regular expression pattern to match invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    # Replace invalid characters with an underscore or another safe character
    sanitized_title: str = re.sub(invalid_chars, "_", title)
    # Remove leading and trailing spaces
    sanitized_title = sanitized_title.strip()
    if sanitized_title.startswith("_"):
        sanitized_title = sanitized_title[1:]

    return (path / sanitized_title).resolve()


def get_final_path(download_path: Path, title: str) -> Path:
    final_path: Path = sanitize_path(download_path, title)
    # Sanitize the path
    if final_path.parent != download_path.resolve():
        raise ValueError("Invalid path", final_path)
    final_path.mkdir(parents=True, exist_ok=True)
    return final_path


async def write_media(media_path: Path, image_content: bytes, url: str) -> None:
    # print(f"[green]Downloading [/]{url}")
    try:
        async with aiofiles.open(media_path, "wb") as f:
            await f.write(image_content)
    except (OSError, FileNotFoundError, TypeError) as e:
        print(f"Failed to write to {media_path} with error: {e}")

    write_to_cache(url)


def get_url_hashfile(url: str) -> Path:
    url_hash: str = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return CACHE_PATH / url_hash


def write_to_cache(url: str) -> None:
    cache_filename: Path = get_url_hashfile(url)
    with open(cache_filename, "w"):
        pass


def get_unique_filename(base_path: Path) -> Path:
    suffix: int = 1
    new_path: Path = base_path.with_stem(f"{base_path.stem}_{suffix}")
    while new_path.exists():
        suffix += 1
        new_path = base_path.with_stem(f"{base_path.stem}_{suffix}")
    return new_path


def main_entry(func) -> Any:
    func.is_main_entry = True
    return func


def exit_session(exit_value: int) -> NoReturn:
    """
    Exit the program with the given exit value.

    Args:
        exit_value (int): The POSIX exit value to exit with.
    """
    # logger.info("End of session")
    # Check if the exit_value is a valid POSIX exit value
    if not 0 <= exit_value <= 255:
        exit_value = EXIT_FAILURE

    if exit_value == EXIT_FAILURE:
        print(
            "\n[red]There were errors during the execution of the script. "
            f"Check the logs at '{LOG_PATH}' for more information.[/]"
        )

    # Exit the program with the given exit value
    sys.exit(exit_value)
