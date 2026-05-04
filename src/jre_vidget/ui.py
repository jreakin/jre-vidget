"""
Rich terminal UI — spinner, progress bar, tables, panels.

See prompts/phase-5-rich-ui/current.md for the full implementation spec.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from pydantic import SecretStr
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    Task,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from jre_vidget.engine import ProgressData, ProgressHook
from jre_vidget.models import (
    BYTES_PER_MB,
    AppConfig,
    BatchJob,
    DownloadResult,
    DownloadStatus,
    VideoFormat,
    VideoInfo,
    VideoPreview,
    YtdlpStatus,
)

# stderr: progress and status do not pollute stdout (agent-friendly / future --json).
console = Console(stderr=True)


def _config_secret_placeholder(secret: SecretStr | None) -> str:
    """Never print secret values in the terminal."""
    if secret is None:
        return "—"
    return "(set)" if secret.get_secret_value() else "—"


def _truncate_url(url: str, max_len: int = 60) -> str:
    if len(url) <= max_len:
        return url
    return f"{url[: max_len - 1]}…"


def _format_upload_date(upload_date: str | None) -> str | None:
    if not upload_date or len(upload_date) != 8:
        return upload_date
    try:
        dt = datetime.strptime(upload_date, "%Y%m%d")
    except ValueError:
        return upload_date
    month = dt.strftime("%b")
    return f"{month} {dt.day} {dt.year}"


def _format_codec_cell(f: VideoFormat) -> str:
    parts: list[str] = []
    if f.vcodec:
        parts.append(f.vcodec)
    if f.acodec:
        parts.append(f.acodec)
    return " / ".join(parts) if parts else "—"


def _format_bitrate_cell(f: VideoFormat) -> str:
    if f.tbr is None:
        return "—"
    return f"{f.tbr:.0f} kbps"


def _format_size_cell(f: VideoFormat) -> str:
    if f.filesize is None:
        return "—"
    mb = f.filesize / BYTES_PER_MB
    return f"~{mb:.0f} MB"


@contextmanager
def spinner(message: str) -> Iterator[None]:
    """Show a Rich spinner while a block executes."""
    with console.status(f"[bold cyan]{message}[/bold cyan]", spinner="dots"):
        yield


def print_preview(meta: VideoPreview) -> None:
    """Render a Rich preview card for a VideoPreview."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="bold cyan", width=14)
    table.add_column("Value")

    table.add_row("Title", meta.title)
    table.add_row("Uploader", meta.uploader)
    table.add_row("Duration", meta.duration_display)
    if meta.view_count is not None:
        table.add_row("Views", f"{meta.view_count:,}")
    if meta.upload_date:
        d = meta.upload_date
        if len(d) == 8:
            table.add_row("Uploaded", f"{d[:4]}-{d[4:6]}-{d[6:]}")
        else:
            table.add_row("Uploaded", d)
    if meta.formats:
        table.add_row("Formats", ", ".join(meta.formats[:6]))
    table.add_row("URL", meta.url)

    console.print(Panel(table, title="[bold]Video Preview[/bold]", border_style="blue"))

    if meta.thumbnail_url:
        console.print(f"\n[dim]Thumbnail:[/dim] {meta.thumbnail_url}")


def print_video_info(info: VideoInfo) -> None:
    """Header panel before download or format listing."""
    udate = _format_upload_date(info.upload_date)
    meta_parts: list[str] = []
    if info.uploader:
        meta_parts.append(info.uploader)
    if udate:
        meta_parts.append(udate)
    meta_parts.append(info.duration_str)
    meta_line = "  ·  ".join(meta_parts) if meta_parts else info.duration_str

    body = (
        f"[bold white]{info.title}[/bold white]\n"
        f"[dim]{meta_line}[/dim]\n"
        f"[dim]{_truncate_url(info.webpage_url or info.url)}[/dim]"
    )
    console.print(Panel(body, border_style="cyan", padding=(0, 1)))


def _formats_table_video(rows: list[VideoFormat]) -> Table:
    table = Table(title="Video Formats")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Resolution")
    table.add_column("FPS")
    table.add_column("Codec")
    table.add_column("Bitrate")
    table.add_column("Size")
    for i, f in enumerate(rows, start=1):
        fps_s = f"{f.fps:g}" if f.fps is not None else "—"
        table.add_row(
            str(i),
            f.resolution or "—",
            fps_s,
            _format_codec_cell(f),
            _format_bitrate_cell(f),
            _format_size_cell(f),
        )
    return table


def _formats_table_audio(rows: list[VideoFormat]) -> Table:
    table = Table(title="[dim]Audio-only formats[/dim]")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Codec", style="dim")
    table.add_column("Bitrate", style="dim")
    table.add_column("Size", style="dim")
    for i, f in enumerate(rows, start=1):
        codec = _format_codec_cell(f)
        table.add_row(
            str(i),
            codec,
            _format_bitrate_cell(f),
            _format_size_cell(f),
        )
    return table


def _progress_task_by_id(progress: Progress, task_id: TaskID) -> Task | None:
    """Resolve a Rich task by stable TaskID (``progress.tasks[i]`` is *not* keyed by id)."""
    for t in progress.tasks:
        if t.id == task_id:
            return t
    return None


def print_formats_table(info: VideoInfo) -> None:
    """Display available video and audio-only formats."""
    video_rows = info.best_formats
    console.print(_formats_table_video(video_rows))

    audio_only = [f for f in info.formats if f.is_audio_only]
    audio_only.sort(key=lambda x: x.tbr or 0, reverse=True)
    if audio_only:
        console.print(_formats_table_audio(audio_only))
    else:
        console.print("[dim]No separate audio-only rows in format list.[/dim]")


def make_progress_hook() -> tuple[ProgressHook, Progress]:
    """
    Return a (hook_fn, progress_context) tuple.

    hook_fn is passed directly to yt-dlp's progress_hooks list.
    progress_context is a Rich Progress instance the caller should use
    as a context manager.
    """
    task_ref: list[TaskID | None] = [None]

    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        DownloadColumn(binary_units=False),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    )

    def hook(d: ProgressData) -> None:
        status = d.get("status")
        if status == YtdlpStatus.ERROR.value:
            err = str(d.get("error") or "Unknown error")
            print_error("Download error", err)
            return

        if status == YtdlpStatus.FINISHED.value:
            tid = task_ref[0]
            if tid is not None:
                task = _progress_task_by_id(progress, tid)
                if task is not None:
                    total = task.total
                    if total is not None and total > 0:
                        progress.update(tid, completed=total)
                    progress.remove_task(tid)
                task_ref[0] = None
            if d.get("filename"):
                console.print("[green]✅ Merging…[/green]")
            return

        if status == YtdlpStatus.DOWNLOADING.value:
            desc = "Downloading"
            fn = d.get("filename")
            if isinstance(fn, str) and fn:
                desc = Path(fn).name

            total = d.get("total_bytes")
            if total is None:
                total = d.get("total_bytes_estimate")

            downloaded = int(d.get("downloaded_bytes") or 0)
            total_i: float | None = float(total) if isinstance(total, (int, float)) else None

            tid = task_ref[0]
            if tid is None:
                task_ref[0] = progress.add_task(desc, total=total_i)
                tid = task_ref[0]
            if tid is None:
                return
            row = _progress_task_by_id(progress, tid)
            if row is None:
                return
            if row.description != desc:
                progress.update(tid, description=desc)
            if total_i is not None and row.total != total_i:
                progress.update(tid, total=total_i)
            progress.update(tid, completed=min(downloaded, int(total_i) if total_i else downloaded))

    return hook, progress


def print_result(result: DownloadResult) -> None:
    """Print outcome of one download (single or batch live line)."""
    if result.status == DownloadStatus.SUCCESS:
        path = str(result.filepath) if result.filepath is not None else "?"
        dur = ""
        if result.duration_s is not None:
            dur = f" ({result.duration_s:.1f}s)"
        console.print(f"[green]✅[/green] {path}{dur}")

    elif result.status == DownloadStatus.FAILED:
        err = result.error or "unknown error"
        body = f"[dim]{result.url}[/dim]\n{err}"
        console.print(
            Panel(
                body,
                title="[red]✗ Failed[/red]",
                border_style="red",
            )
        )

    else:
        console.print(f"[yellow]⚠[/yellow] Skipped: [dim]{result.url}[/dim]")


def print_batch_summary(job: BatchJob) -> None:
    """Final summary table after a batch run."""
    skipped = sum(1 for r in job.results if r.status == DownloadStatus.SKIPPED)
    table = Table(title="Batch Summary")
    table.add_column("URL", overflow="ellipsis", max_width=36)
    table.add_column("Status")
    table.add_column("File", overflow="ellipsis", max_width=28)

    for r in job.results:
        url_disp = _truncate_url(r.url, 40)
        if r.status == DownloadStatus.SUCCESS:
            status_cell = "[green]✅ done[/green]"
            file_cell = str(r.filepath) if r.filepath else "—"
        elif r.status == DownloadStatus.FAILED:
            status_cell = "[red]❌ fail[/red]"
            file_cell = (r.error or "—")[:40]
        else:
            status_cell = "[yellow]⚠ skip[/yellow]"
            file_cell = "—"
        table.add_row(url_disp, status_cell, file_cell)

    console.print(table)
    footer = f"  {job.total} total  ·  {job.completed} completed  ·  {job.failed} failed"
    if skipped:
        footer += f"  ·  {skipped} skipped"
    console.print(f"[dim]{footer}[/dim]")


def print_config(config: AppConfig) -> None:
    """Show config as a styled table."""
    table = Table(title="vidget configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")
    table.add_row("output_dir", str(config.output_dir))
    table.add_row("quality", config.quality.value)
    table.add_row("format", config.format.value)
    table.add_row("subtitles", str(config.subtitles))
    table.add_row("max_concurrent", str(config.max_concurrent))
    table.add_row("auth.client_id", config.auth.client_id or "—")
    table.add_row("auth.client_secret", _config_secret_placeholder(config.auth.client_secret))
    table.add_row("auth.refresh_token", _config_secret_placeholder(config.auth.refresh_token))
    console.print(table)


def print_error(message: str, detail: str | None = None) -> None:
    """Styled error panel."""
    body = f"[bold]{message}[/bold]"
    if detail:
        body += f"\n{detail}"
    console.print(
        Panel(
            body.strip(),
            title="[red]Error[/red]",
            border_style="red",
        )
    )


def print_warning(message: str) -> None:
    """Non-fatal warning line."""
    console.print(f"[yellow]{message}[/yellow]")


def print_success(message: str) -> None:
    """Success confirmation line."""
    console.print(f"[green]{message}[/green]")


def print_batch_intro(count: int) -> None:
    """Announce how many URLs were read for batch."""
    console.print(f"Found {count} URL(s)")
