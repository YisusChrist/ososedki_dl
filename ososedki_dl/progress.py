"""Download progress bar."""

from pathlib import Path
from typing import Optional

import requests  # type: ignore
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    ProgressColumn,
)


class PercentageColumn(ProgressColumn):
    def render(self, task) -> str:
        return f"{task.percentage:>5.1f}%"


def download(
    url: str, filename: Path, headers: Optional[dict[str, str]] = None
) -> Path:
    # Streaming, so we can iterate over the response.
    response: requests.Response = requests.get(url, headers=headers, stream=True)

    # Sizes in bytes.
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024

    progress = Progress(
        TextColumn("[bold blue]{task.fields[filename]}"),
        BarColumn(bar_width=None),  # Stretch the bar to fit the available width
        PercentageColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )

    with progress:
        task = progress.add_task(
            "Downloading", filename=filename.name, total=total_size
        )

        with open(filename, "wb") as file:
            for data in response.iter_content(block_size):
                file.write(data)
                progress.update(task, advance=len(data))

    if total_size != 0 and progress.tasks[task].completed != total_size:
        raise RuntimeError("Could not download file")

    return filename
