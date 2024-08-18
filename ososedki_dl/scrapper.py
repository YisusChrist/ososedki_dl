"""Scrapper module for downloading images from various websites."""

from pathlib import Path
from typing import Awaitable, Callable
from importlib import import_module

from aiohttp import ClientSession
from rich.console import Console
from rich.progress import Progress, TaskID

console = Console()


# Mapping of domain patterns to their respective module and function names
downloaders: dict[str, tuple[str, str]] = {
    "https://bunkr-albums.io": (
        "ososedki_dl.crawlers.bunkrr_albums",
        "find_albums",
    ),
    "https://eromexxx.com": (
        "ososedki_dl.crawlers.eromexxx",
        "download_profile",
    ),
    "https://fapello.is": (
        "ososedki_dl.crawlers.fapello_is",
        "download_profile",
    ),
    "https://ososedki.com": (
        "ososedki_dl.crawlers.ososedki",
        "download_album",
    ),
    "https://sorrymother.to": (
        "ososedki_dl.crawlers.sorrymother",
        "download_album",
    ),
    "https://wildskirts.com": (
        "ososedki_dl.crawlers.wildskirts",
        "download_profile",
    ),
}


def print_errors(results: list[dict[str, str]]) -> None:
    console.print("Errors:")
    for result in results:
        if "error" in result["status"]:
            console.print(f"[red]{result['url']}[/]: {result['status']}")


async def generic_download(
    session: ClientSession, urls: list[str], download_path: Path
) -> None:
    with Progress() as progress:
        task: TaskID = progress.add_task("[cyan]Downloading...", total=len(urls))

        results: list[dict[str, str]] = []
        for url in urls:
            await handle_downloader(
                session=session,
                download_path=download_path,
                progress=progress,
                task=task,
                results=results,
                url=url,
            )

        ok_count: int = sum(1 for result in results if result["status"] == "ok")
        skipped_count: int = sum(
            1 for result in results if result["status"] == "skipped"
        )
        error_count: int = sum(1 for result in results if "error" in result["status"])

        console.print(
            f"""\n
[green]Downloaded: {ok_count}[/]
[yellow]Skipped: {skipped_count}[/]
[red]Errors: {error_count}[/]\n"""
        )

        if error_count > 0:
            print_errors(results)


async def handle_downloader(
    session: ClientSession,
    download_path: Path,
    progress: Progress,
    task: TaskID,
    results: list[dict[str, str]],
    url: str,
) -> None:
    for pattern, (module_name, function_name) in downloaders.items():
        if url.startswith(pattern):
            result: list[dict[str, str]] = await dynamic_download(
                session=session,
                album_url=url,
                download_path=download_path,
                progress=progress,
                task=task,
                module_name=module_name,
                function_name=function_name,
            )
            results.extend(result)
            break
    else:
        console.print(f"[yellow]No downloader found for URL: {url}[/]")


async def dynamic_download(
    session: ClientSession,
    album_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
    module_name: str,
    function_name: str,
) -> list[dict[str, str]]:
    module = import_module(module_name)
    download_func = getattr(module, function_name)

    result: list[dict[str, str]] = await download_func(
        session, album_url, download_path, progress, task
    )

    progress.advance(task)
    return result
