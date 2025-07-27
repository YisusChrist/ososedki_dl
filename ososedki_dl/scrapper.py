"""Scrapper module for downloading images from various websites."""

import importlib
import inspect
import pkgutil
from collections import defaultdict
from pathlib import Path
from types import ModuleType
from typing import DefaultDict

from aiohttp import ClientResponse, ClientSession
from rich.console import Console
from rich.progress import Progress, TaskID

console = Console()
crawler_modules: list[ModuleType] = []


def get_crawler_modules() -> list[ModuleType]:
    return crawler_modules


def print_errors(results: list[dict[str, str]], verbose: bool = False) -> None:
    """
    Print a summary of the errors encountered during the download process.

    Args:
        results (list[dict[str, str]]): The list of results.
        verbose (bool, optional): Whether to print the full error messages. Defaults to False.
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
    console.print("[bold yellow]Grouped Errors Summary:[/]")
    for error_type, urls in error_groups.items():
        console.print(f"[red]{error_type} - Count: {len(urls)}[/]")
        if verbose:
            console.print("Affected URLs:")
            for url in urls:
                console.print(f"  • {url}")

    print()


def load_crawler_modules() -> None:
    """Dynamically load all modules in the given package."""
    global crawler_modules

    crawlers_package: str = "ososedki_dl.crawlers"
    package: ModuleType = importlib.import_module(crawlers_package)

    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        if module_name.startswith("_") or module_name == "pinterest":
            continue
        full_module_name: str = f"{crawlers_package}.{module_name}"
        module: ModuleType = importlib.import_module(full_module_name)
        crawler_modules.append(module)


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
    global crawler_modules

    for module in crawler_modules:
        download_url: str = module.DOWNLOAD_URL
        if download_url and url.startswith(download_url):
            result: list[dict[str, str]] = await dynamic_download(
                session=session,
                album_url=url,
                download_path=download_path,
                progress=progress,
                task=task,
                module=module,
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
    module: ModuleType,
) -> list[dict[str, str]]:
    # Use inspect.getmembers to find the function marked with is_main_entry
    download_func = next(
        (
            func
            for _, func in inspect.getmembers(module, inspect.isfunction)
            if getattr(func, "is_main_entry", False)
        ),
        None,
    )

    if not download_func:
        raise ValueError(f"No main entry function found in module {module.__name__}")

    # Check if the URL is valid
    try:
        response: ClientResponse = await session.get(album_url)
        response.raise_for_status()
    except Exception as e:
        return [{"url": album_url, "status": f"error: {e}"}]

    result: list[dict[str, str]] = await download_func(
        session, album_url, download_path, progress, task
    )

    progress.advance(task)
    return result
