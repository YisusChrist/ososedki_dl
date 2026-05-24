"""Async download progress bar."""

from __future__ import annotations

from rich.progress import (BarColumn, DownloadColumn, MofNCompleteColumn,
                           Progress, SpinnerColumn, TaskProgressColumn,
                           TextColumn, TimeElapsedColumn, TimeRemainingColumn,
                           TransferSpeedColumn)

from .consts import PERCENTAGE_FORMAT


def MediaProgress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn(
            "{task.fields[filename]}",
            style="bold blue",
            # table_column=Column(width=40, no_wrap=True),
        ),
        BarColumn(bar_width=None),
        TaskProgressColumn(PERCENTAGE_FORMAT),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
    )


def AlbumProgress() -> Progress:
    return Progress(
        TextColumn(
            "{task.description}",
            style="cyan",
            # table_column=Column(width=40, no_wrap=True),
        ),
        BarColumn(bar_width=None),
        TaskProgressColumn(PERCENTAGE_FORMAT),
        MofNCompleteColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
    )
