"""Typer CLI — delegates to engine; display via Rich (console / tables)."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

import typer
from rich.console import Console
from rich.table import Table

from jre_vidget import engine, ui
from jre_vidget.models import (
    AppConfig,
    BatchJob,
    DownloadConfig,
    DownloadStatus,
    OutputFormat,
    Quality,
    VideoFormat,
    VideoInfo,
)

app = typer.Typer(
    name="vidget",
    help="🎬  Download & convert videos from 1000+ sites.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()
config_app = typer.Typer(help="View or edit default settings.")
app.add_typer(config_app, name="config")


T = TypeVar("T")


def _resolve(value: T | None, default: T) -> T:
    """Return value if set, otherwise fall back to default."""
    return value if value is not None else default


def _read_batch_urls(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    urls: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        urls.append(s)
    return urls


def _format_codec_row(f: VideoFormat) -> str:
    parts: list[str] = []
    if f.vcodec:
        parts.append(f.vcodec)
    if f.acodec:
        parts.append(f.acodec)
    return " / ".join(parts) if parts else "—"


def _format_bitrate(f: VideoFormat) -> str:
    if f.tbr is None:
        return "—"
    return f"{f.tbr:.0f} kbps"


def _formats_table(title: str, rows: list[VideoFormat]) -> Table:
    table = Table(title=title)
    table.add_column("Format ID", style="cyan")
    table.add_column("Resolution")
    table.add_column("FPS")
    table.add_column("Codec")
    table.add_column("Bitrate")
    table.add_column("Size")
    for f in rows:
        fps_s = f"{f.fps:g}" if f.fps is not None else "—"
        table.add_row(
            f.format_id,
            f.resolution or "—",
            fps_s,
            _format_codec_row(f),
            _format_bitrate(f),
            f.display_size,
        )
    return table


@app.command()
def download(
    url: str = typer.Argument(..., help="Video page URL to download"),
    quality: Quality | None = typer.Option(
        None,
        "--quality",
        "-q",
        help="best | 1080p | 720p | 480p | audio",
    ),
    out_format: OutputFormat | None = typer.Option(
        None,
        "--format",
        "-f",
        help="mp4 | mp3 | mkv | m4a | …",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory",
    ),
    subs: bool = typer.Option(False, "--subs", help="Download subtitles if available"),
) -> None:
    """Download a single video."""
    cfg = AppConfig.load()
    resolved_quality = _resolve(quality, cfg.quality)
    resolved_format = _resolve(out_format, cfg.format)
    resolved_output = _resolve(output, cfg.output_dir)
    resolved_subs = subs if subs else cfg.subtitles

    dl_cfg = DownloadConfig(
        url=url,
        quality=resolved_quality,
        format=resolved_format,
        output_dir=resolved_output,
        subtitles=resolved_subs,
    )

    try:
        result = engine.download(dl_cfg, progress_hook=ui.make_progress_hook())
    except engine.EngineError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e

    if result.status == DownloadStatus.SUCCESS:
        path = result.filepath if result.filepath is not None else "(unknown path)"
        console.print(f"[green]Downloaded:[/green] {path}")
        return

    console.print(f"[red]Download failed:[/red] {result.error or 'unknown error'}")
    raise typer.Exit(code=1)


@app.command()
def batch(
    file: Path = typer.Argument(..., help="Text file with one URL per line"),
    quality: Quality | None = typer.Option(None, "--quality", "-q"),
    out_format: OutputFormat | None = typer.Option(None, "--format", "-f"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    subs: bool = typer.Option(False, "--subs"),
) -> None:
    """Download all URLs listed in a text file (one per line)."""
    if not file.is_file():
        console.print(f"[red]File not found:[/red] {file}")
        raise typer.Exit(code=1)

    urls = _read_batch_urls(file)
    console.print(f"Found {len(urls)} URL(s)")

    cfg = AppConfig.load()
    base = DownloadConfig(
        url="",
        quality=_resolve(quality, cfg.quality),
        format=_resolve(out_format, cfg.format),
        output_dir=_resolve(output, cfg.output_dir),
        subtitles=subs if subs else cfg.subtitles,
    )
    job = BatchJob(urls=urls, config=base)
    engine.download_batch(job, progress_hook=ui.make_progress_hook(), on_result=ui.print_result)

    console.print(f"Done: [green]{job.completed}[/green] ok, [red]{job.failed}[/red] failed")


@app.command()
def formats(
    url: str = typer.Argument(..., help="Video page URL to inspect"),
) -> None:
    """List available formats for a URL."""
    try:
        with console.status("Fetching format info…", spinner="dots"):
            info = engine.fetch_info(url)
    except engine.EngineError as e:
        console.print(f"[red]Could not fetch info:[/red] {e}")
        raise typer.Exit(code=1) from e

    _print_video_summary(info)
    console.print(_formats_table("Video (best per resolution)", info.best_formats))

    audio_only = [f for f in info.formats if f.is_audio_only]
    audio_only.sort(key=lambda x: x.tbr or 0, reverse=True)
    if audio_only:
        console.print(_formats_table("Audio-only", audio_only))
    else:
        console.print("[dim]No separate audio-only rows in format list.[/dim]")


def _print_video_summary(info: VideoInfo) -> None:
    console.print(f"[bold]{info.title}[/bold]")
    if info.uploader:
        console.print(f"Uploader: {info.uploader}")
    console.print(f"Duration: {info.duration_str}")


@config_app.command("show")
def config_show() -> None:
    """Print current saved configuration."""
    cfg = AppConfig.load()
    table = Table(title="vidget configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")
    table.add_row("output_dir", str(cfg.output_dir))
    table.add_row("quality", cfg.quality.value)
    table.add_row("format", cfg.format.value)
    table.add_row("subtitles", str(cfg.subtitles))
    table.add_row("max_concurrent", str(cfg.max_concurrent))
    console.print(table)


@config_app.command("set")
def config_set(
    output: Path | None = typer.Option(None, "--output", help="Default output directory"),
    quality: Quality | None = typer.Option(None, "--quality", help="Default quality"),
    out_format: OutputFormat | None = typer.Option(
        None,
        "--format",
        help="Default output format",
    ),
    subs: bool | None = typer.Option(None, "--subs/--no-subs"),
) -> None:
    """Update stored defaults (only specified options change)."""
    cfg = AppConfig.load()
    changed: list[str] = []

    if output is not None:
        cfg.output_dir = output
        changed.append(f"output_dir={output}")
    if quality is not None:
        cfg.quality = quality
        changed.append(f"quality={quality.value}")
    if out_format is not None:
        cfg.format = out_format
        changed.append(f"format={out_format.value}")
    if subs is not None:
        cfg.subtitles = subs
        changed.append(f"subtitles={subs}")

    if not changed:
        console.print("[yellow]No options given; nothing to update.[/yellow]")
        raise typer.Exit(code=0)

    cfg.save()
    console.print("[green]Updated:[/green] " + ", ".join(changed))
