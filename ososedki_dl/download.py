"""Download module for the application."""

from __future__ import annotations

import sys
from asyncio import sleep
from dataclasses import dataclass
from hashlib import sha256
from mimetypes import guess_extension
from pathlib import Path
from ssl import SSLCertVerificationError
from time import monotonic
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlparse

import aiofiles
from aiohttp.client import ClientResponse, ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError
from aiohttp_client_cache.response import CachedResponse
from aiohttp_client_cache.session import CachedSession
from core_helpers.logs import logger
from rich import print

from .consts import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_RESPONSE_PROPERTY,
    KB,
    MAX_SLEEP_SECONDS,
    MAX_TIMEOUT,
)
from .progress import MediaProgress
from .utils import get_unique_filename, get_url_hashfile, sanitize_path, write_to_cache

if TYPE_CHECKING:
    from typing import Any

if sys.version_info >= (3, 10):
    SessionType = CachedSession | ClientSession
    ResponseType = ClientResponse | CachedResponse
else:
    from typing import Union

    SessionType = Union[CachedSession, ClientSession]
    ResponseType = Union[ClientResponse, CachedResponse]


def _choose_chunk_size(
    throughput_bps: int | None = None,
    min_kb: int = 32,
    max_kb: int = KB,
    target_ms: int = 150,
) -> int:
    logger.debug(
        f"Choosing chunk size with throughput_bps={throughput_bps}, "
        f"min_kb={min_kb}, max_kb={max_kb}, target_ms={target_ms}"
    )

    # throughput_bps is bytes/sec (measure it once you start receiving data)
    if not throughput_bps:
        return 64 * KB  # default before we can measure
    target_bytes = int(throughput_bps * (target_ms / 1000))
    # clamp to [min_kb, max_kb]
    return max(min_kb * KB, min(target_bytes, max_kb * KB))


@dataclass
class Downloader:
    session: SessionType
    headers: dict[str, str] | None = None
    check_cache: bool = False
    debug: bool = False
    timeout = ClientTimeout(total=MAX_TIMEOUT)

    def __post_init__(self) -> None:
        logger.debug("Initialized Downloader")

    async def fetch(
        self,
        url: str,
        method: str = "GET",
        response_property: str = DEFAULT_RESPONSE_PROPERTY,
        raw_response: bool = False,
        **kwargs: Any,
    ) -> Any:
        """
        Fetches a URL with retries and error handling.

        This method implements robust fetching logic with retries for transient
        errors, SSL error handling, and dynamic response property access. It
        also supports returning the raw response object if needed.

        Args:
            url (str): The URL to fetch.
            method (str, optional): The HTTP method to use. Defaults to "GET".
            response_property (str, optional): The property of the response to
                return (e.g., "text", "json", "content"). Defaults to "text".
            raw_response (bool, optional): If True, return the raw response object
                instead of a property. Defaults to False.
            **kwargs: Additional keyword arguments to pass to the request method.

        Returns:
            Any: The requested property of the response, or the raw response if
            raw_response is True.
        """
        method = method.upper()
        logger.debug(
            f"{method} URL: {url} with response_property='{response_property}' "
            f"and raw_response={raw_response}"
        )

        # Merge headers: priority to kwargs, fallback to instance defaults
        headers = kwargs.pop("headers", self.headers)

        max_attempts = 5
        attempt = 0
        while True:
            attempt += 1
            try:
                response = await self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=self.timeout,
                    **kwargs,
                )
                if isinstance(response, CachedResponse) and self.debug:
                    print(
                        f"URL: {url}\n",
                        f"from_cache: {response.from_cache}",
                        f"created_at: {response.created_at}",
                        f"expires: {response.expires}",
                        f"is_expired: {response.is_expired}",
                    )
                if response.status in (429, 503):
                    # Too Many Requests or Service Unavailable
                    if attempt >= max_attempts:
                        response.raise_for_status()
                    await sleep(min(2**attempt, MAX_SLEEP_SECONDS))
                    continue

                response.raise_for_status()
                logger.debug(f"Response status for {url}: {response.status}")

                if raw_response:
                    return response

                # Dynamically access the specified response property
                if hasattr(response, response_property):
                    attr = getattr(response, response_property)
                    return await attr() if callable(attr) else attr
                raise ValueError(
                    f"Response object has no property '{response_property}'"
                )

            except SSLCertVerificationError as e:
                logger.exception(f"SSL certificate verification failed for {url}")
                print(
                    f"SSL error for {url}: {e}. Retrying with SSL verification disabled..."
                )
                kwargs["ssl"] = False
                if attempt >= max_attempts:
                    raise
            except ClientConnectorError as e:
                logger.exception(f"Failed to connect to {url}")
                print(f"Failed to connect to {url} with error {e}. Retrying...")
                if attempt >= max_attempts:
                    raise
                await sleep(min(2**attempt, MAX_SLEEP_SECONDS))
            except ClientResponseError as e:  # 4xx, 5xx errors
                logger.exception(f"Failed to fetch {url}")
                print(f"Failed to fetch {url} with status {e.status}")
                if attempt >= max_attempts:
                    raise

    async def download_image(
        self, url: str, response: ResponseType, media_path: Path
    ) -> tuple[str, Path]:
        """
        Handles reading image bytes and checking for duplicates.

        Args:
            url (str): The URL of the image to download.
            response (ResponseType): The aiohttp response object for the image URL.
            media_path (Path): The target file path to save the downloaded image.

        Returns:
            tuple[str, Path]: A tuple containing the download status ("ok" or "skipped"
            and the final path of the downloaded image.
        """
        logger.debug(f"Downloading image from URL: {url}")

        image_content: bytes = await response.read()

        if media_path.exists():
            logger.debug(f"Checking existing file: {media_path}")
            file_content: bytes = media_path.read_bytes()
            if file_content == image_content:
                return "skipped", media_path
            media_path = get_unique_filename(media_path)
            logger.debug(f"File exists, renaming to: {media_path}")

        async with aiofiles.open(media_path, "wb") as f:
            await f.write(image_content)

        return "ok", media_path

    async def download_video(
        self,
        url: str,
        response: ResponseType,
        media_path: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        dynamic_chunk: bool = False,
    ) -> tuple[str, Path]:
        """
        Handles streaming video chunks, tracking progress, and validating hashes.

        Args:
            url (str): The URL of the video to download.
            response (ResponseType): The aiohttp response object for the video URL.
            media_path (Path): The target file path to save the downloaded video.
            chunk_size (int, optional): The initial size of each chunk to download.
                Defaults to DEFAULT_CHUNK_SIZE.
            dynamic_chunk (bool, optional): Whether to adjust chunk size dynamically
                based on observed throughput. Defaults to False.

        Returns:
            tuple[str, Path]: A tuple containing the download status ("ok" or "skipped")
            and the final path of the downloaded video.
        """
        logger.debug(f"Downloading video from URL: {url}")

        content_length = int(response.headers.get("Content-Length", 0))
        logger.debug(f"Content length: {content_length} bytes")

        temp_path: Path = media_path.with_suffix(media_path.suffix + ".part")
        logger.debug(f"Temporary file path: {temp_path}")

        remote_hash = sha256()
        bytes_seen = 0
        t0: float = monotonic()
        if dynamic_chunk:
            chunk_size = _choose_chunk_size()

        with MediaProgress() as progress:
            task = progress.add_task(
                "Downloading", filename=media_path.name, total=content_length
            )
            p_task = progress.tasks[0]
            async with aiofiles.open(temp_path, "wb") as f:
                logger.debug(f"Opened temporary file for writing: {temp_path}")
                async for chunk in response.content.iter_chunked(chunk_size):
                    if not chunk:
                        continue

                    remote_hash.update(chunk)
                    await f.write(chunk)
                    progress.advance(task, len(chunk))
                    logger.debug(
                        f"Wrote {len(chunk)} bytes to {temp_path.name}, "
                        f"Total written: {p_task.completed}/{p_task.total}"
                    )

                    if not dynamic_chunk:
                        continue

                    now: float = monotonic()
                    bytes_seen += len(chunk)
                    elapsed: float = now - t0
                    if elapsed > 1.0:  # update once per second (cheap)
                        throughput_bps = int(bytes_seen / elapsed)
                        chunk_size = _choose_chunk_size(throughput_bps)  # 32KB..1MB
                        logger.debug(
                            f"Throughput: {throughput_bps / KB:.2f} KB/s, "
                            f"Chunk size: {chunk_size / KB:.2f} KB"
                        )
                        print(f"New chunk size: {chunk_size / KB:.2f} KB")
                        bytes_seen = 0
                        t0 = now

        # Duplicate check using hashes
        if media_path.exists():
            logger.debug(f"File exists. Calculating local hash for: {media_path}")
            local_hash = sha256()

            # Read the existing local file in chunks asynchronously
            async with aiofiles.open(media_path, "rb") as f:
                while local_chunk := await f.read(chunk_size):
                    local_hash.update(local_chunk)

            if local_hash.digest() == remote_hash.digest():
                logger.info(f"File already exists and matches: {media_path}")
                temp_path.unlink(missing_ok=True)
                logger.debug(f"Removed temporary file: {temp_path}")
                return "skipped", media_path

        final_path: Path = get_unique_filename(media_path)
        logger.debug(f"Final file path: {final_path}")
        temp_path.rename(final_path)

        return "ok", final_path

    async def download_and_save_media(
        self, url: str, album_path: Path
    ) -> dict[str, str]:
        """
        Downloads media from the given URL and saves it to the specified album
        path.

        This method determines the media type (image or video) based on the
        content type and delegates to the appropriate download method. It also
        handles caching and returns a standardized result dictionary.

        Args:
            url (str): The URL of the media to download.
            album_path (Path): The directory path where the media should be saved.

        Returns:
            dict[str, str]: A dictionary containing the URL and the download status
            ("ok", "skipped", or "error: <message>").
        """
        logger.debug(f"Downloading media from URL: {url}")

        if self.check_cache and get_url_hashfile(url).exists():
            logger.info(f"Media already in cache, skipping download: {url}")
            return {"url": url, "status": "skipped"}

        # Use urlparse to extract the media name from the URL
        media_name: str = unquote(urlparse(url).path).split("/")[-1]

        try:
            response = await self.fetch(url, raw_response=True)
        except ClientResponseError as e:
            logger.exception(f"Failed to fetch {url}")
            return {"url": url, "status": f"error: {e.status}"}
        except Exception as e:
            logger.exception(f"Failed to fetch {url}")
            return {"url": url, "status": f"error: {e}"}

        content_type: str = response.headers.get("Content-Type", "")

        if not Path(media_name).suffix:
            logger.info(
                f"Media name '{media_name}' has no extension, checking content type..."
            )
            if not content_type:
                logger.error(f"Failed to get content type for {url}")
                print(f"ERROR: Failed to get content type for {url}")
                return {"url": url, "status": "error: missing content type"}

            # Map content type to a file extension
            extension: str | None = guess_extension(content_type.split(";")[0].strip())
            if not extension:
                logger.error(
                    f"Failed to guess extension for content type: {content_type}"
                )
                print(
                    f"ERROR: Failed to guess extension for content type: {content_type}"
                )
                return {"url": url, "status": "error: missing content type"}

            media_name += extension
            logger.debug(f"Updated media name to: {media_name}")

        media_path: Path = sanitize_path(album_path, media_name)
        logger.debug(f"Media path resolved to: {media_path}")

        if "mp4" in content_type or "video" in content_type:
            status, final_path = await self.download_video(url, response, media_path)
        else:
            status, final_path = await self.download_image(url, response, media_path)

        if status == "ok":
            if self.check_cache:
                write_to_cache(url)
            logger.info(f"Downloaded media to: {final_path}")
        elif status == "skipped":
            logger.info(f"File already exists and matches: {media_path}")

        return {"url": url, "status": status}
