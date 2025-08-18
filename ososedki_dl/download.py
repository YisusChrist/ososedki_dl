"""Download module for the application."""

from __future__ import annotations

import hashlib
from asyncio import sleep
from pathlib import Path
from ssl import SSLCertVerificationError
from time import monotonic
from typing import TYPE_CHECKING, Union
from urllib.parse import unquote, urlparse

import aiofiles
import requests
from aiohttp import (ClientConnectorError, ClientResponseError, ClientSession,
                     ClientTimeout)
from aiohttp_client_cache.session import CachedSession
from rich import print

from ososedki_dl.progress import MediaProgress

from .consts import CHECK_CACHE, MAX_TIMEOUT
from .utils import (get_unique_filename, get_url_hashfile, sanitize_path,
                    write_to_cache)

if TYPE_CHECKING:
    from typing import Any, Optional

    from aiohttp import ClientResponse


client_timeout = ClientTimeout()
SessionType = Union[CachedSession, ClientSession]


def _choose_chunk_size(
    throughput_bps: Optional[int] = None,
    min_kb: int = 32,
    max_kb: int = 1024,
    target_ms: int = 150,
) -> int:
    # throughput_bps is bytes/sec (measure it once you start receiving data)
    if not throughput_bps:
        return 64 * 1024  # default before we can measure
    target_bytes = int(throughput_bps * (target_ms / 1000))
    # clamp to [min_kb, max_kb]
    return max(min_kb * 1024, min(target_bytes, max_kb * 1024))


async def fetch(
    session: SessionType,
    url: str,
    response_property: str = "text",
    raw_response: bool = False,
    **kwargs: Any,
) -> Any:
    while True:
        try:
            response = await session.get(url=url, timeout=client_timeout, **kwargs)
            if response.status in (429, 503):
                # Too Many Requests or Service Unavailable
                await sleep(5)
                continue
            response.raise_for_status()

            if raw_response:
                return response

            # Dynamically access the specified response property
            if hasattr(response, response_property):
                return await getattr(response, response_property)()
            raise ValueError(f"Response object has no property '{response_property}'")

        except SSLCertVerificationError as e:
            raise e
        except ClientConnectorError as e:
            print(f"Failed to connect to {url} with error {e}. Retrying...")
            await sleep(5)
        except ClientResponseError as e:  # 4xx, 5xx errors
            print(f"Failed to fetch {url} with status {e.status}")
            response2: requests.Response = requests.get(
                url, timeout=MAX_TIMEOUT, **kwargs
            )
            response2.raise_for_status()
            if raw_response:
                return response2

            # Dynamically access the specified response property
            if hasattr(response2, response_property):
                return getattr(response2, response_property)()
            return response2.content


async def download_image(
    url: str, response: ClientResponse, media_path: Path
) -> dict[str, str]:
    image_content: bytes = await response.read()

    if media_path.exists():
        file_content: bytes = media_path.read_bytes()
        if file_content == image_content:
            #print(f"Skipping {url}")
            return {"url": url, "status": "skipped"}
        media_path = get_unique_filename(media_path)

    async with aiofiles.open(media_path, "wb") as f:
        await f.write(image_content)

    write_to_cache(url)
    #print(f"Downloaded {url}")
    return {"url": url, "status": "ok"}


async def download_video(
    url: str,
    response: ClientResponse,
    media_path: Path,
    chunk_size: int = 8192,
    dynamic_chunk: bool = False,
) -> dict[str, str]:
    content_length = int(response.headers.get("Content-Length", 0))

    remote_hash = hashlib.sha256()
    file_exists: bool = media_path.exists()
    local_hash = hashlib.sha256() if file_exists else None

    temp_path: Path = media_path.with_suffix(media_path.suffix + ".part")

    bytes_seen = 0
    t0: float = monotonic()
    if dynamic_chunk:
        chunk_size = _choose_chunk_size()

    with MediaProgress() as progress:
        task = progress.add_task(
            "Downloading", filename=media_path.name, total=content_length
        )
        async with aiofiles.open(temp_path, "wb") as f:
            async for chunk in response.content.iter_chunked(chunk_size):
                if not chunk:
                    continue

                remote_hash.update(chunk)
                await f.write(chunk)
                progress.advance(task, len(chunk))

                if local_hash is not None:
                    local_hash.update(chunk)

                if not dynamic_chunk:
                    continue

                now: float = monotonic()
                bytes_seen += len(chunk)
                elapsed: float = now - t0
                if elapsed > 1.0:  # update once per second (cheap)
                    throughput_bps = int(bytes_seen / elapsed)
                    chunk_size = _choose_chunk_size(throughput_bps)  # 32KB..1MB
                    print(f"New chunk size: {chunk_size / 1024:.2f} KB")
                    bytes_seen = 0
                    t0 = now

    if file_exists and local_hash and local_hash.digest() == remote_hash.digest():
        temp_path.unlink(missing_ok=True)
        #print(f"Skipping {url}")
        return {"url": url, "status": "skipped"}

    new_path: Path = get_unique_filename(media_path)
    temp_path.rename(new_path)
    write_to_cache(url)
    #print(f"Downloaded {url}")
    return {"url": url, "status": "ok"}


async def download_and_compare(
    session: SessionType,
    url: str,
    media_path: Path,
    headers: Optional[dict[str, str]] = None,
) -> dict[str, str]:
    if CHECK_CACHE and get_url_hashfile(url).exists():
        #print(f"Skipping {url}")
        return {"url": url, "status": "skipped"}
    try:
        response = await fetch(session, url, raw_response=True, headers=headers)
    except ClientResponseError as e:
        #print(f"Failed to fetch {url} with status {e.status}")
        return {"url": url, "status": f"error: {e.status}"}
    except Exception as e:
        #print(f"Failed to fetch {url} with error {e}")
        return {"url": url, "status": f"error: {e}"}

    content_type: str = response.headers.get("Content-Type", "")
    if "mp4" in content_type or "video" in content_type:
        return await download_video(url, response, media_path)
    else:
        return await download_image(url, response, media_path)


async def download_and_save_media(
    session: SessionType,
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
        content_type: str | None = response.headers.get("Content-Type")
        if not content_type:
            print(f"Failed to get content type for {url}")
        else:
            # Map content type to a file extension
            extension: str = content_type.split("/")[-1]  # e.g., 'image/jpeg' -> 'jpeg'
            media_name = f"{media_name}.{extension}"

    media_path: Path = sanitize_path(album_path, media_name)

    if not headers and "sorrymother.video" in url:
        headers = {
            "Range": "bytes=0-",
            "Referer": "https://sorrymother.to/",
        }
    elif "nice-try.fckthots.xyz" in url:
        headers = {"Referer": "https://fapello.is/"}

    return await download_and_compare(
        session,
        url,
        media_path,
        headers,
    )
