"""``vidget download`` command."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from jre_vidget import cli_common as cc
from jre_vidget.config import load_app_config
from jre_vidget.models import (
    DownloadConfig,
    DownloadResult,
    DownloadStatus,
    OutputFormat,
    PrivacyStatus,
    PublishResult,
    Quality,
    VideoInfo,
)


def _warn_metadata_fetch_failed(exc: cc.engine.EngineError, *, json_output: bool) -> None:
    if json_output:
        sys.stderr.write(f"warning: could not fetch video info: {exc}\n")
    else:
        cc.console.print(f"[yellow]Warning:[/yellow] Could not fetch video info: {exc}")


def load_video_info_for_publish(url: str, *, json_output: bool) -> VideoInfo | None:
    """Fetch :class:`VideoInfo` for publish title fallback; logs and returns ``None`` on engine errors."""
    try:
        return cc.engine.fetch_info(url)
    except cc.engine.EngineError as e:
        _warn_metadata_fetch_failed(e, json_output=json_output)
        return None


def run_engine_download(dl_cfg: DownloadConfig, *, json_output: bool) -> DownloadResult:
    """Run :func:`engine.download` with optional Rich progress (disabled for ``--json``)."""
    with cc.progress_hook_session(json_output=json_output) as hook:
        return cc.engine.download(dl_cfg, progress_hook=hook)


def emit_download_json_stdout(
    result: DownloadResult,
    pub_result: PublishResult | None,
) -> None:
    """Emit the machine-readable download (and optional publish) payload."""
    out: dict[str, object] = {"download": result.model_dump(mode="json")}
    if pub_result is not None:
        out["publish"] = pub_result.model_dump(mode="json")
    typer.echo(json.dumps(out, default=str))


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
    subs: bool | None = typer.Option(
        None,
        "--subs/--no-subs",
        help="Download subtitles (default: saved config).",
    ),
    publish_flag: bool = typer.Option(
        False,
        "--publish",
        help="Upload to YouTube after download.",
    ),
    pub_title: str | None = typer.Option(
        None,
        "--title",
        help="YouTube title (default: scraped title).",
    ),
    pub_description: str = typer.Option(
        "",
        "--description",
        help="YouTube description.",
    ),
    pub_privacy: PrivacyStatus = typer.Option(
        PrivacyStatus.PUBLIC,
        "--privacy",
        help="YouTube privacy: public, unlisted, or private.",
    ),
    pub_remove: bool = typer.Option(
        False,
        "--remove",
        help="Delete local file after upload.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit only JSON on stdout (download result; includes publish when --publish).",
    ),
) -> None:
    """Download a single video."""
    cfg = load_app_config()
    dl_cfg = cc.resolve_download_config(cfg, quality, out_format, output, subs, url)

    video_info = None
    if publish_flag:
        video_info = load_video_info_for_publish(url, json_output=json_output)

    try:
        result = run_engine_download(dl_cfg, json_output=json_output)
    except KeyboardInterrupt:
        cc.ui.print_error("Download cancelled.", "Ctrl-C received.")
        raise typer.Exit(code=130) from None
    except cc.engine.EngineError as e:
        if json_output:
            sys.stderr.write(f"download error: {e}\n")
        else:
            cc.ui.print_error("Error", str(e))
        raise typer.Exit(code=1) from e

    if not json_output:
        cc.ui.print_result(result)

    if result.status != DownloadStatus.SUCCESS:
        if json_output:
            emit_download_json_stdout(result, None)
        raise typer.Exit(code=1)

    pub_result = None
    if publish_flag:
        pub_result = cc.publish_after_download(
            cfg,
            result,
            options=cc.PublishOptions(
                title=pub_title,
                description=pub_description,
                privacy=pub_privacy,
                remove_after_upload=pub_remove,
            ),
            video_info=video_info,
            url=url,
            json_output=json_output,
        )

    if json_output:
        emit_download_json_stdout(result, pub_result)
    elif pub_result is not None:
        cc.console.print(f"[green]✓[/green] Published: {pub_result.url}")
        if pub_result.removed_local_file:
            cc.console.print(f"  Local file removed: {result.filepath}")
