from __future__ import annotations

import asyncio
import csv
import hashlib
import statistics as stats
import tempfile
import time
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from aiohttp import ClientSession, ClientTimeout
from rich import print
from rich.progress import (BarColumn, DownloadColumn, Progress, SpinnerColumn,
                           TimeElapsedColumn, TimeRemainingColumn,
                           TransferSpeedColumn)
from rich.traceback import install

from ososedki_dl.progress import PercentageColumn

# ---------------------------
# Config
# ---------------------------
DEFAULT_TIMEOUT = ClientTimeout(
    total=None, connect=30
)  # no total cap; adjust if you want
SAMPLE_PERIOD_S = 0.25  # sampling cadence for throughput rows
EMA_ALPHA = 0.2  # smoothing factor for EMA throughput
OUT_DIR = Path("bench_results")  # where CSVs will be stored
OUT_DIR.mkdir(exist_ok=True)
KB = 1024
MB = KB * KB


@dataclass
class BenchResult:
    url: str
    chunk_size: int
    status: str
    total_bytes: int
    duration_s: float
    mean_bps: float
    p50_bps: float
    p95_bps: float
    max_bps: float
    samples_csv: Path
    summary_row: dict[str, str | int | float]


async def _download_with_metrics(
    session: ClientSession,
    url: str,
    chunk_size: int,
    run_no: int,
    headers: Optional[dict[str, str]] = None,
    sample_period_s: float = SAMPLE_PERIOD_S,
    ema_alpha: float = EMA_ALPHA,
) -> BenchResult:
    """
    Stream-downloads `url` with `chunk_size`, sampling throughput every ~sample_period_s.
    Writes per-sample CSV with columns:
    time_s, bytes_cum, bytes_since_last_sample, inst_bps, ema_bps, chunk_size
    """
    # Output file paths
    safe_name: str = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    suffix: str = f"r{run_no}_t{time.time_ns()}"
    run_id: str = f"{safe_name}_cs{chunk_size}_{suffix}"
    samples_csv: Path = OUT_DIR / f"samples_{run_id}.csv"

    total_bytes: int = 0
    ema_bps: float | None = None
    last_sample_t: float = time.perf_counter()
    last_sample_bytes: int = 0
    inst_bps_series: list[float] = []

    t0: float = time.perf_counter()
    try:
        async with session.get(url, timeout=DEFAULT_TIMEOUT, headers=headers) as resp:
            resp.raise_for_status()
            total_len = int(resp.headers.get("Content-Length", 0)) or None

            with (
                Progress(
                    SpinnerColumn(),
                    "[progress.description]{task.description}",
                    BarColumn(bar_width=None),
                    PercentageColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                    TimeElapsedColumn(),
                    transient=True,
                ) as progress,
                tempfile.TemporaryDirectory() as temp_dir,
                open(Path(temp_dir) / f"{run_id}.part", "wb") as f,
                open(samples_csv, "w", newline="") as csvfile,
            ):
                writer = csv.writer(csvfile)
                writer.writerow(
                    [
                        "time_s",
                        "bytes_cum",
                        "bytes_delta",
                        "inst_bps",
                        "ema_bps",
                        "chunk_size",
                    ]
                )

                task = progress.add_task(
                    f"Chunk {chunk_size / KB:.2f} KiB", total=total_len
                )

                async for chunk in resp.content.iter_chunked(chunk_size):
                    if not chunk:
                        continue
                    n: int = len(chunk)
                    total_bytes += n
                    f.write(chunk)
                    progress.advance(task, n)

                    # sampling
                    now: float = time.perf_counter()
                    if now - last_sample_t >= sample_period_s:
                        bytes_delta: int = total_bytes - last_sample_bytes
                        inst_bps: float = bytes_delta / (now - last_sample_t)
                        inst_bps_series.append(inst_bps)
                        ema_bps = (
                            inst_bps
                            if ema_bps is None
                            else (ema_alpha * inst_bps + (1 - ema_alpha) * ema_bps)
                        )

                        writer.writerow(
                            [
                                f"{now - t0:.3f}",
                                total_bytes,
                                bytes_delta,
                                f"{inst_bps:.3f}",
                                f"{ema_bps:.3f}",
                                chunk_size,
                            ]
                        )

                        last_sample_t = now
                        last_sample_bytes = total_bytes

        status: str = "ok"
    except Exception as e:
        status = f"error: {e}"

    duration_s: float = time.perf_counter() - t0

    # Compute metrics
    mean_bps: float = (total_bytes / duration_s) if duration_s > 0 else 0.0
    p50_bps: float = stats.median(inst_bps_series) if inst_bps_series else 0.0
    p95_bps: float = (  # 95th percentile
        stats.quantiles(inst_bps_series, n=100, method="inclusive")[94]
        if inst_bps_series
        else 0.0
    )
    max_bps: float = max(inst_bps_series) if inst_bps_series else 0.0

    summary_row: dict[str, str | int | float] = dict(
        url=url,
        chunk_size=chunk_size,
        status=status,
        total_bytes=total_bytes,
        duration_s=round(duration_s, 3),
        mean_bps=round(mean_bps, 1),
        p50_bps=round(p50_bps, 1),
        p95_bps=round(p95_bps, 1),
        max_bps=round(max_bps, 1),
        samples_csv=str(samples_csv),
    )

    return BenchResult(
        url=url,
        chunk_size=chunk_size,
        status=status,
        total_bytes=total_bytes,
        duration_s=duration_s,
        mean_bps=mean_bps,
        p50_bps=p50_bps,
        p95_bps=p95_bps,
        max_bps=max_bps,
        samples_csv=samples_csv,
        summary_row=summary_row,
    )


async def bench_url(
    url: str,
    chunk_sizes: Iterable[int],
    runs_per_size: int,
    headers: Optional[dict[str, str]] = None,
) -> None:
    """
    Benchmarks a single URL for multiple chunk sizes. Writes a per-URL summary
    CSV to the `bench_results` directory and prints its path.
    """
    rows: list[dict[str, str | int | float]] = []
    async with ClientSession() as session:
        for cs in chunk_sizes:
            for r in range(1, runs_per_size + 1):
                print(
                    f"[cyan]→ Benchmarking[/cyan] chunk_size={cs / KB:.2f} "
                    f"KiB (run {r}/{runs_per_size})"
                )
                res: BenchResult = await _download_with_metrics(
                    session, url, cs, r, headers=headers
                )
                status_color: str = "green" if res.status == "ok" else "red"
                print(
                    f"[{status_color}]{res.status}[/] "
                    f"chunk_size={cs / KB:.2f} "
                    f"KiB total={res.total_bytes / KB:.2f} KiB "
                    f"time={res.duration_s:.3f} s "
                    f"mean={res.mean_bps / MB:.2f} MiB/s"
                )
                rows.append(res.summary_row)

    if not rows:
        print("[yellow]No benchmark rows collected; skipping summary write.[/yellow]")
        return

    # Write / append summary
    summary_csv: Path = (
        OUT_DIR / f"summary_{hashlib.sha256(url.encode()).hexdigest()[:16]}.csv"
    )
    write_header: bool = not summary_csv.exists()
    with open(summary_csv, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        if write_header:
            w.writeheader()
        w.writerows(rows)

    print(f"[bold]Summary written:[/bold] {summary_csv}")


def get_parsed_args() -> Namespace:
    start_chunk_size = 8 * KB  # 8 KiB
    default_chunk_sizes: list[int] = [start_chunk_size * (2**i) for i in range(6, 9)]

    p = ArgumentParser(description="Benchmark streaming download chunk sizes.")
    sub = p.add_subparsers(dest="mode", required=True)

    run: ArgumentParser = sub.add_parser("run", help="Run benchmarks")
    run.add_argument("url", help="URL to download for benchmarking")
    run.add_argument(
        "--chunk-sizes",
        nargs="+",
        type=int,
        default=default_chunk_sizes,
        help="Chunk sizes in bytes",
    )
    run.add_argument(
        "--runs-per-size",
        type=int,
        default=1,
        help="Repeat each chunk size this many times",
    )
    run.add_argument(
        "--header",
        action="append",
        default=[],
        help="HTTP header key:value (can repeat)",
    )

    plot: ArgumentParser = sub.add_parser("plot", help="Plot results")
    plot.add_argument(
        "--samples",
        nargs="+",
        required=False,
        help="samples_*.csv files to plot (if omitted, plot all in bench_results/)",
    )
    return p.parse_args()


def plot_samples(samples: list[str]) -> None:
    import matplotlib.pyplot as plt

    if not samples:
        # If no specific samples provided, plot all in OUT_DIR
        samples = [str(p) for p in OUT_DIR.glob("samples_*.csv")]

    if not samples:
        print("[bold]No sample CSVs found to plot.[/bold] Please run benchmarks first.")
        return

    for p in samples:
        p = Path(p)
        times: list[float] = []
        inst: list[float] = []
        ema: list[float] = []
        with open(p, newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                times.append(float(row["time_s"]))
                inst.append(float(row["inst_bps"]) / MB)  # MiB/s
                ema.append(float(row["ema_bps"]) / MB)  # MiB/s
        label = p.name.replace("samples_", "").replace(".csv", "")
        plt.figure()
        plt.title(f"Throughput over time: {label}")
        plt.plot(times, inst, label="Instant throughput (MiB/s)")
        plt.plot(times, ema, label="EMA throughput (MiB/s)")
        plt.xlabel("Time (s)")
        plt.ylabel("Throughput (MiB/s)")
        plt.legend()
        plt.tight_layout()
        plt.show()


def main() -> None:
    install()
    args: Namespace = get_parsed_args()

    if args.mode == "run":
        print(
            f"[bold]Running benchmark for URL:[/bold] [link={args.url}]{args.url}[/link]"
        )

        headers: Optional[dict[str, str]] = None
        if args.header:
            headers = {}
            for kv in args.header:
                if ":" not in kv:
                    raise SystemExit(f"Bad header '{kv}', expected key:value")
                k, v = kv.split(":", 1)
                headers[k.strip()] = v.strip()

        asyncio.run(
            bench_url(
                args.url,
                args.chunk_sizes,
                args.runs_per_size,
                headers,
            )
        )
    elif args.mode == "plot":
        print("[bold]Plotting sample throughput graphs...[/bold]")
        plot_samples(args.samples)


if __name__ == "__main__":
    main()
