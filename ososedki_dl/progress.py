"""Async download progress bar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.progress import (BarColumn, DownloadColumn, Progress, ProgressColumn,
                           SpinnerColumn, TextColumn, TimeElapsedColumn,
                           TimeRemainingColumn, TransferSpeedColumn)

if TYPE_CHECKING:
    from rich.progress import TaskID


class PercentageColumn(ProgressColumn):
    def render(self, task: TaskID) -> str:
        return f"{task.percentage:>5.1f}%"


def MediaProgress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.fields[filename]}"),
        BarColumn(bar_width=None),
        PercentageColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
    )


def AlbumProgress() -> Progress:
    return Progress(
        TextColumn("[cyan]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>5.1f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TransferSpeedColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    )
