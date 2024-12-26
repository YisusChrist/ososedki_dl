"""Download module for the application."""

from asyncio import sleep
from pathlib import Path
from ssl import SSLCertVerificationError
from typing import Any, Optional
from urllib.parse import unquote, urlparse

import requests
from aiohttp import (ClientConnectorError, ClientResponseError, ClientSession,
                     ClientTimeout, InvalidURL)
from bs4 import BeautifulSoup
from fake_useragent import UserAgent  # type: ignore
from rich import print

from ososedki_dl.utils import (get_unique_filename, get_url_hashfile,
                               sanitize_path, write_media)

from .consts import CHECK_CACHE, MAX_TIMEOUT

client_timeout = ClientTimeout()
ua = UserAgent(min_version=120.0)
_user_agent: str = ""


def get_user_agent() -> str:
    global _user_agent

    if _user_agent == "":
        _user_agent = ua.random
    return _user_agent


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
        headers: dict[str, str] = {"User-Agent": get_user_agent()}

        # Update the headers from the kwargs
        kwargs["headers"] = headers

    while True:
        try:
            async with session.get(
                url=url, timeout=client_timeout, **kwargs
            ) as response:
                if (
                    response.status == 429 or response.status == 503
                ):  # Too Many Requests or Service Unavailable
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

        except SSLCertVerificationError as e:
            raise e
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
