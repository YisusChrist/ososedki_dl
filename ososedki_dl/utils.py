import hashlib
import re
from asyncio import sleep
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote, urlparse

import aiofiles  # type: ignore
import requests  # type: ignore
import validators  # type: ignore
from aiohttp import (
    ClientConnectorError,
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    InvalidURL,
)
from bs4 import BeautifulSoup  # type: ignore
from fake_useragent import UserAgent  # type: ignore
from rich import print
from rich.prompt import Prompt

from .consts import CACHE_PATH, CHECK_CACHE, MAX_TIMEOUT

ua = UserAgent(min_version=120.0)
client_timeout = ClientTimeout()


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


def get_user_input() -> tuple[list, Path]:
    print("\n", end="")
    url: list = get_valid_url()
    path: Path = get_valid_path()
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


async def get_soup(session: ClientSession, url: str) -> BeautifulSoup:
    html_content: str = await fetch(session, url)
    return BeautifulSoup(html_content, "html.parser")


async def _generic_fetch(
    session: ClientSession,
    url: str,
    response_property: str = "text",
    **kwargs: Any,
) -> Any:
    if not kwargs.get("headers"):
        headers: dict[str, str] = {"User-Agent": ua.random}

        # Update the headers from the kwargs
        kwargs["headers"] = headers

    while True:
        try:
            async with session.get(
                url=url, timeout=client_timeout, **kwargs
            ) as response:
                if response.status == 429:  # Too many requests
                    await sleep(5)
                    continue
                response.raise_for_status()

                # Dynamically access the specified response property
                if hasattr(response, response_property):
                    return await getattr(response, response_property)()
                else:
                    raise ValueError(
                        f"Response object has no property '{response_property}'"
                    )

        except ClientConnectorError as e:
            print(f"Failed to connect to {url} with error {e}. Retrying...")
            await sleep(5)

        except ClientResponseError as e:  # 4xx, 5xx errors
            print(f"Failed to fetch {url} with status {e.status}")
            response = requests.get(url, timeout=MAX_TIMEOUT, **kwargs)
            response.raise_for_status()

            # Dynamically access the specified response property
            if hasattr(response, response_property):
                return getattr(response, response_property)()
            else:
                return response.content


async def fetch(
    session: ClientSession,
    url: str,
    property: str = "text",
    **kwargs: Optional[dict[str, str]],
) -> Any:
    return await _generic_fetch(
        session=session, url=url, response_property=property, **kwargs
    )


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


async def download_and_compare(
    session: ClientSession,
    url: str,
    media_path: Path,
    headers: Optional[dict[str, str]] = None,
) -> dict[str, str]:
    if CHECK_CACHE:
        # check if the link is in the cache
        cache_filename: Path = get_url_hashfile(url)
        if cache_filename.exists():
            print(f"Skipping {url}")
            return {"url": url, "status": "skipped"}
    try:
        image_content: bytes = await fetch(
            session=session,
            url=url,
            property="read",
            headers=headers,
        )
    except ClientResponseError as e:
        print(f"Failed to fetch {url} with status {e.status}")
        return {"url": url, "status": f"error: {e.status}"}
    except InvalidURL as e:
        print(f'Invalid URL: "{url}"')
        return {"url": url, "status": f"error: {e}"}
    except Exception as e:
        print(f"Failed to fetch {url} with error {e}")
        return {"url": url, "status": f"error: {e}"}

    if media_path.exists():
        file_content: bytes = media_path.read_bytes()
        if file_content == image_content:
            print(f"Skipping {url}")
            return {"url": url, "status": "skipped"}
        else:
            new_path: Path = get_unique_filename(media_path)
            await write_media(new_path, image_content, url)
    else:
        await write_media(media_path, image_content, url)

    print(f"Downloaded {url}")
    return {"url": url, "status": "ok"}


async def download_and_save_media(
    session: ClientSession,
    url: str,
    album_path: Path,
    headers: Optional[dict[str, str]] = None,
) -> dict[str, str]:
    # Use urlparse to extract the media name from the URL
    media_name: str = unquote(urlparse(url).path).split("/")[-1]
    if not Path(media_name).suffix:
        # If media_name has no extension, add one using the url content type
        response: requests.Response = requests.head(
            url, headers=headers, timeout=MAX_TIMEOUT
        )
        content_type: str = response.headers.get("Content-Type")
        if not content_type:
            print(f"Failed to get content type for {url}")
        else:
            # Map content type to a file extension
            extension = content_type.split("/")[-1]  # e.g., 'image/jpeg' -> 'jpeg'
            media_name = f"{media_name}.{extension}"

    media_path: Path = sanitize_path(album_path, media_name)

    if not headers and "sorrymother.video" in url:
        headers = {
            "Range": "bytes=0-",
            "Referer": "https://sorrymother.to/",
        }

    return await download_and_compare(
        session,
        url,
        media_path,
        headers,
    )


def main_entry(func) -> Any:
    func.is_main_entry = True
    return func
