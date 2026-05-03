"""Typer CLI — delegates to engine; display via Rich in ui.py."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

import typer

from jre_vidget import engine, ui
from jre_vidget.models import (
    AppConfig,
    BatchJob,
    DownloadConfig,
    DownloadStatus,
    OutputFormat,
    Quality,
)

app = typer.Typer(
    name="vidget",
    help="🎬  Download & convert videos from 1000+ sites.",
    add_completion=False,
    no_args_is_help=True,
)
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

    hook, progress_ctx = ui.make_progress_hook()
    try:
        with progress_ctx:
            result = engine.download(dl_cfg, progress_hook=hook)
    except engine.EngineError as e:
        ui.print_error("Error", str(e))
        raise typer.Exit(code=1) from e

    ui.print_result(result)
    if result.status == DownloadStatus.SUCCESS:
        return

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
        ui.print_error("File not found", str(file))
        raise typer.Exit(code=1)

    urls = _read_batch_urls(file)
    ui.print_batch_intro(len(urls))

    cfg = AppConfig.load()
    base = DownloadConfig(
        url="",
        quality=_resolve(quality, cfg.quality),
        format=_resolve(out_format, cfg.format),
        output_dir=_resolve(output, cfg.output_dir),
        subtitles=subs if subs else cfg.subtitles,
    )
    job = BatchJob(urls=urls, config=base)
    hook, progress_ctx = ui.make_progress_hook()
    with progress_ctx:
        engine.download_batch(job, progress_hook=hook, on_result=ui.print_result)

    ui.print_batch_summary(job)


@app.command()
def formats(
    url: str = typer.Argument(..., help="Video page URL to inspect"),
) -> None:
    """List available formats for a URL."""
    try:
        with ui.spinner("Fetching video info…"):
            info = engine.fetch_info(url)
    except engine.EngineError as e:
        ui.print_error("Could not fetch info", str(e))
        raise typer.Exit(code=1) from e

    ui.print_video_info(info)
    ui.print_formats_table(info)


@config_app.command("show")
def config_show() -> None:
    """Print current saved configuration."""
    cfg = AppConfig.load()
    ui.print_config(cfg)


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
        ui.print_warning("No options given; nothing to update.")
        raise typer.Exit(code=0)

    cfg.save()
    ui.print_success("Updated: " + ", ".join(changed))
