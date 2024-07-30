from pathlib import Path
from typing import Awaitable, Callable

from aiohttp import ClientSession
from rich.console import Console
from rich.progress import Progress, TaskID

console = Console()


def print_errors(results: list[dict[str, str]]) -> None:
    console.print("\nErrors:")
    for result in results:
        if "error" in result["status"]:
            console.print(f"[red]{result['url']}[/]: {result['status']}")


async def generic_download(
    session: ClientSession,
    urls: list[str],
    download_path: Path,
    download_func: Callable[
        [ClientSession, str, Path, Progress, TaskID], Awaitable[list[dict[str, str]]]
    ],
) -> None:
    with Progress() as progress:
        task: TaskID = progress.add_task("[cyan]Downloading...", total=len(urls))

        results: list[dict[str, str]] = []
        for url in urls:
            result: list[dict[str, str]] = await download_func(
                session, url, download_path, progress, task
            )
            results.extend(result)

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


async def _generic_callback(
    callback: Callable[
        [ClientSession, str, Path, Progress, TaskID], Awaitable[list[dict[str, str]]]
    ],
    session: ClientSession,
    url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = await callback(
        session, url, download_path, progress, task
    )
    progress.advance(task)
    return result


async def eromexxx_download(
    session: ClientSession,
    album_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    from ososedki_dl.crawlers.eromexxx import download_profile

    return await _generic_callback(
        download_profile,
        session,
        album_url,
        download_path,
        progress,
        task,
    )


async def ososedki_download(
    session: ClientSession,
    album_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    from ososedki_dl.crawlers.ososedki import download_album

    return await _generic_callback(
        download_album,
        session,
        album_url,
        download_path,
        progress,
        task,
    )


async def sorrymother_download(
    session: ClientSession,
    album_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    from ososedki_dl.crawlers.sorrymother import download_album

    return await _generic_callback(
        download_album,
        session,
        album_url,
        download_path,
        progress,
        task,
    )


async def wildskirts_download(
    session: ClientSession,
    album_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    from ososedki_dl.crawlers.wildskirts import download_profile

    return await _generic_callback(
        download_profile,
        session,
        album_url,
        download_path,
        progress,
        task,
    )


async def fapello_is_download(
    session: ClientSession,
    album_url: str,
    download_path: Path,
    progress: Progress,
    task: TaskID,
) -> list[dict[str, str]]:
    from ososedki_dl.crawlers.fapello_is import download_profile

    return await _generic_callback(
        download_profile,
        session,
        album_url,
        download_path,
        progress,
        task,
    )


# Mapping of domain patterns to their respective download functions
downloaders: dict[str, Callable] = {
    "https://eromexxx.com": eromexxx_download,
    "https://fapello.is": fapello_is_download,
    "https://ososedki.com": ososedki_download,
    "https://sorrymother.to": sorrymother_download,
    "https://wildskirts.com": wildskirts_download,
}
