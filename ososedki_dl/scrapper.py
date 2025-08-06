"""Scrapper module for downloading images from various websites."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from rich import print
from rich.progress import Progress

from .crawlers import CrawlerContext
from .crawlers import crawlers as crawler_modules

if TYPE_CHECKING:
    from pathlib import Path
    from typing import DefaultDict

    from aiohttp import ClientResponse
    from aiohttp_client_cache.response import CachedResponse
    from rich.progress import TaskID

    from .crawlers import CrawlerInstance
    from .download import SessionType


def print_errors(results: list[dict[str, str]], verbose: bool = False) -> None:
    """
    Print a summary of the errors encountered during the download process.

    Args:
        results (list[dict[str, str]]): The list of results.
        verbose (bool, optional): Whether to print the full error messages.
            Defaults to False.
    """

    # Group errors by error message
    error_groups: DefaultDict[str, list[str]] = defaultdict(list)

    for result in results:
        if "error" in result["status"]:
            # Extract the main error message without the specific URL
            error_msg: str = result["status"].split("url:", 1)[0].strip()
            if "Failed to resolve" in error_msg:
                error_msg = "Name Resolution Error - Failed to resolve host"
            elif "404 Client Error: Not Found" in error_msg:
                error_msg = "404 Client Error: Not Found"
            elif "sun9-" in error_msg:
                error_msg = "SUN9 Error - Failed to fetch"
            else:
                error_msg = error_msg.split(":", 1)[0].strip()

            error_groups[error_msg].append(result["url"])

    # Print grouped errors
    print("[bold yellow]Grouped Errors Summary:[/]")
    for error_type, urls in error_groups.items():
        print(f"[red]{error_type} - Count: {len(urls)}[/]")
        if verbose:
            print("Affected URLs:")
            for url in urls:
                print(f"  • {url}")

    print()


async def generic_download(
    session: SessionType, urls: list[str], download_path: Path
) -> None:
    with Progress() as progress:
        task: TaskID = progress.add_task("[cyan]Downloading...", total=len(urls))
        context = CrawlerContext(session, download_path, progress, task)

        results: list[dict[str, str]] = []
        for url in urls:
            await handle_downloader(
                context=context,
                results=results,
                url=url,
            )

        ok_count: int = sum(1 for result in results if result["status"] == "ok")
        skipped_count: int = sum(
            1 for result in results if result["status"] == "skipped"
        )
        error_count: int = sum(1 for result in results if "error" in result["status"])

        print(
            f"""\n
[green]Downloaded: {ok_count}[/]
[yellow]Skipped: {skipped_count}[/]
[red]Errors: {error_count}[/]\n"""
        )

        if error_count > 0:
            print_errors(results)


async def handle_downloader(
    context: CrawlerContext, results: list[dict[str, str]], url: str
) -> None:
    """
    Selects and invokes the appropriate crawler to download content from the
    given URL.

    If a matching crawler is found based on the URL prefix, it instantiates the
    crawler with the provided context and performs the download, appending the
    results to the shared results list. If no suitable crawler is found, a
    warning is printed.

    Args:
        context (CrawlerContext): The context containing session, download
            path, progress bar, and task ID.
        results (list[dict[str, str]]): The list to append download results to.
        url (str): The URL to download from.
    """
    for CrawlerClass in crawler_modules:
        if url.startswith(CrawlerClass.site_url):
            crawler: CrawlerInstance = CrawlerClass(context)
            result: list[dict[str, str]] = await dynamic_download(context, url, crawler)
            results.extend(result)
            break
    else:
        print(f"[yellow]No downloader found for URL: {url}[/]")


async def dynamic_download(
    context: CrawlerContext, album_url: str, crawler: CrawlerInstance
) -> list[dict[str, str]]:
    """
    Download images from the specified album URL using the provided crawler.

    Attempts to fetch the album URL to ensure it is accessible before invoking
    the crawler's download method. If the URL is invalid or the request fails,
    returns an error result. Advances the progress bar after completion.

    Args:
        album_url (str): The URL of the album to download.
        crawler (CrawlerInstance): The crawler instance responsible for
            downloading from the album URL.

    Returns:
        list[dict[str, str]]: A list of result dictionaries indicating the
        outcome of the download operation.
    """
    # Check if the URL is valid
    try:
        response: ClientResponse | CachedResponse = await context.session.get(album_url)
        response.raise_for_status()
    except Exception as e:
        return [{"url": album_url, "status": f"error: {e}"}]

    result: list[dict[str, str]] = await crawler.download(album_url)

    context.progress.advance(context.task)
    return result
