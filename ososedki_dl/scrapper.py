"""Scrapper module for downloading images from various websites."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import TYPE_CHECKING

from rich import print

from .crawlers import crawlers as crawler_modules

if TYPE_CHECKING:
    from pathlib import Path

    from aiohttp import ClientResponse
    from aiohttp_client_cache.response import CachedResponse

    from .crawlers import CrawlerInstance
    from .download import SessionType


def normalize_error_message(raw_status: str) -> str:
    # Extract after "error:" if present
    if "error:" in raw_status:
        raw_status = raw_status.split("error:", 1)[1].strip()

    # Common known patterns
    if "Failed to resolve" in raw_status:
        return "Name Resolution Error - Failed to resolve host"
    if "404 Client Error: Not Found" in raw_status:
        return "404 Client Error: Not Found"
    if "sun9-" in raw_status:
        return "SUN9 Error - Failed to fetch"

    # Default fallback: take the text before the first ":"
    return raw_status.split(":", 1)[0].strip()


def print_error_report_card(error_groups: dict[str, list[str]]) -> None:
    total: int = sum(len(urls) for urls in error_groups.values())
    unique: int = len(error_groups)

    print("[bold magenta]===== Error Report Card =====[/]")
    print(f"Total Errors: {total}")
    print(f"Unique Error Types: {unique}\n")

    print("Top Issues:")
    for err, urls in sorted(error_groups.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  • {err} ({len(urls)})")
    print()


def print_errors(results: list[dict[str, str]]) -> None:
    """
    Print a summary of the errors encountered during the download process.

    Args:
        results (list[dict[str, str]]): The list of results.
    """
    # Extract only errors with normalized message
    errors: list[tuple[str, str]] = [
        (normalize_error_message(r["status"]), r["url"])
        for r in results
        if r["status"].startswith("error")
    ]

    # Group errors by error message
    error_groups: defaultdict[str, list[str]] = defaultdict(list)
    for err, url in errors:
        error_groups[err].append(url)

    print_error_report_card(error_groups)


async def generic_download(
    session: SessionType, urls: list[str], download_path: Path
) -> None:
    """
    Download images from a list of URLs using the appropriate crawler.

    Args:
        session (SessionType): The HTTP session to use for requests.
        urls (list[str]): List of URLs to download images from.
        download_path (Path): The base path where downloaded media will be saved.
    """
    results: list[dict[str, str]] = []
    for url in urls:
        results.extend(await handle_downloader(session, download_path, url))

    status_counts = Counter(result["status"].split(":")[0] for result in results)

    print(
        f"""
[green]Downloaded: {status_counts['ok']}[/]
[yellow]Skipped: {status_counts['skipped']}[/]
[red]Errors: {status_counts['error']}[/]\n"""
    )

    if status_counts['error'] > 0:
        print_errors(results)


async def handle_downloader(
    session: SessionType, download_path: Path, url: str
) -> list[dict[str, str]]:
    """
    Selects and invokes the appropriate crawler to download content from the
    given URL.

    If a matching crawler is found based on the URL prefix, it instantiates the
    crawler with the provided context and performs the download, appending the
    results to the shared results list. If no suitable crawler is found, a
    warning is printed.

    Args:
        session (SessionType): The HTTP session to use for requests.
        download_path (Path): The base path where downloaded media will be saved.
        url (str): The URL to download from.

    Returns:
        list[dict[str, str]]: The list to append download results to.
    """
    # Check if the URL is valid
    try:
        response: ClientResponse | CachedResponse = await session.get(url)
        response.raise_for_status()
    except Exception as e:
        return [{"url": url, "status": f"error: {e}"}]

    for CrawlerClass in crawler_modules:
        if url.startswith(CrawlerClass.site_url):
            crawler: CrawlerInstance = CrawlerClass(session, download_path)
            return await crawler.download(url)
    else:
        print(f"[yellow]No downloader found for URL: {url}[/]")
        return [{"url": url, "status": "error: no downloader found"}]
