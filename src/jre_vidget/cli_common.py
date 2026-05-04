"""Shared CLI helpers; command modules import engine/auth/etc. from here for one patch target."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import typer
from rich.console import Console

from jre_vidget import auth, checks, engine, publisher, ui
from jre_vidget import config as vidget_config
from jre_vidget.auth import AuthError
from jre_vidget.models import (
    AppConfig,
    DownloadConfig,
    DownloadResult,
    OutputFormat,
    PrivacyStatus,
    PublishConfig,
    PublishResult,
    Quality,
    VideoInfo,
)
from jre_vidget.publisher import PublishError

console = Console()

_logging_configured = False


def _log_level_from_env() -> int:
    """Resolve ``VIDGET_LOG_LEVEL`` to a ``logging`` module level constant."""
    raw = os.getenv("VIDGET_LOG_LEVEL", "WARNING").strip()
    name = raw.upper() if raw else "WARNING"
    candidate = getattr(logging, name, logging.WARNING)
    return candidate if isinstance(candidate, int) else logging.WARNING


def _ensure_cli_logging() -> None:
    """Apply ``logging.basicConfig`` once per process from ``VIDGET_LOG_LEVEL``."""
    global _logging_configured
    if _logging_configured:
        return
    logging.basicConfig(level=_log_level_from_env())
    _logging_configured = True


def _is_headless() -> bool:
    """True when stdin is not a TTY (pipelines, CI, Typer CliRunner)."""
    return not sys.stdin.isatty()


def _parse_privacy(value: str) -> PrivacyStatus:
    """Validate CLI / workflow privacy string → :class:`PrivacyStatus` with a stable error message."""
    try:
        return PrivacyStatus(value)
    except ValueError:
        raise typer.BadParameter("privacy must be public, unlisted, or private") from None


def _resolve_download_config(
    cfg: AppConfig,
    quality: Quality | None,
    out_format: OutputFormat | None,
    output: Path | None,
    subs: bool | None,
    url: str,
    *,
    max_concurrent: int | None = None,
) -> DownloadConfig:
    """Merge CLI overrides with saved defaults (``subs`` uses tri-state: None → config)."""
    resolved_quality = quality if quality is not None else cfg.quality
    resolved_format = out_format if out_format is not None else cfg.format
    resolved_output = _validate_output(output if output is not None else cfg.output_dir)
    resolved_subs = cfg.subtitles if subs is None else subs
    kwargs: dict[str, object] = {
        "url": url,
        "quality": resolved_quality,
        "format": resolved_format,
        "output_dir": resolved_output,
        "subtitles": resolved_subs,
    }
    if max_concurrent is not None:
        kwargs["max_concurrent"] = max_concurrent
    return DownloadConfig.model_validate(kwargs)


def _read_batch_urls(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    urls: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        urls.append(s)
    return urls


def _is_remote_publish_target(target: str) -> bool:
    t = target.strip()
    return t.startswith(("http://", "https://"))


def _dispatch_publish_workflow(
    *,
    url: str,
    title: str,
    description: str,
    privacy: PrivacyStatus,
    remove_after_upload: bool,
) -> None:
    """Trigger ``publish.yml`` via the GitHub CLI (``gh`` must be installed and authenticated)."""
    cmd = [
        "gh",
        "workflow",
        "run",
        "publish.yml",
        "-f",
        f"url={url}",
        "-f",
        f"title={title}",
        "-f",
        f"description={description}",
        "-f",
        f"privacy={privacy.value}",
        "-f",
        f"remove_after_upload={'true' if remove_after_upload else 'false'}",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError as e:
        msg = "Install the GitHub CLI (https://cli.github.com/) and ensure it is on PATH."
        raise RuntimeError(msg) from e
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or e.stdout or "").strip() or str(e)
        raise RuntimeError(detail) from e


def _validate_output(path: Path) -> Path:
    """Ensure the path exists or can be created, and is writable."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        ui.print_error(f"Cannot write to {path}", "Check directory permissions.")
        raise typer.Exit(code=1) from None
    return path


@dataclass(frozen=True)
class PublishOptions:
    """YouTube publish fields collected from the download command."""

    title: str | None
    description: str
    privacy: PrivacyStatus
    remove_after_upload: bool


def _resolve_publish_title_for_download(
    options: PublishOptions,
    *,
    video_info: VideoInfo | None,
    fallback_url: str,
) -> str:
    """Pick title: explicit CLI title, else scraped title, else the source URL."""
    if options.title:
        return options.title
    if video_info is not None:
        return video_info.title
    return fallback_url


def _publish_config_for_downloaded_file(
    filepath: Path,
    options: PublishOptions,
    *,
    video_info: VideoInfo | None,
    url: str,
) -> PublishConfig:
    """Build :class:`PublishConfig` after a successful download."""
    title = _resolve_publish_title_for_download(
        options,
        video_info=video_info,
        fallback_url=url,
    )
    return PublishConfig(
        filepath=filepath,
        title=title,
        description=options.description,
        privacy=options.privacy,
        remove_after_upload=options.remove_after_upload,
    )


def _publish_after_download(
    cfg: AppConfig,
    result: DownloadResult,
    *,
    options: PublishOptions,
    video_info: VideoInfo | None,
    url: str,
    json_output: bool = False,
) -> PublishResult:
    """Upload the downloaded file to YouTube. Exits the process on auth or upload errors."""
    fp = result.filepath
    if fp is None:
        msg = "Download reported success but no output file path was recorded; cannot publish."
        if json_output:
            sys.stderr.write(f"publish error: {msg}\n")
        else:
            ui.print_error("Cannot publish", msg)
        raise typer.Exit(code=1)
    publish_config = _publish_config_for_downloaded_file(
        fp,
        options,
        video_info=video_info,
        url=url,
    )
    try:
        with console.status("Uploading to YouTube…"):
            return publisher.upload(publish_config, cfg.auth)
    except AuthError as e:
        console.print(f"[red]YouTube auth error:[/red] {e}")
        raise typer.Exit(code=3) from e
    except PublishError as e:
        console.print(f"[red]YouTube upload failed:[/red] {e}")
        raise typer.Exit(code=1) from e


__all__ = [
    "AuthError",
    "PublishError",
    "PublishOptions",
    "_dispatch_publish_workflow",
    "_ensure_cli_logging",
    "_is_headless",
    "_parse_privacy",
    "_publish_after_download",
    "_publish_config_for_downloaded_file",
    "_read_batch_urls",
    "_resolve_download_config",
    "_resolve_publish_title_for_download",
    "_validate_output",
    "auth",
    "checks",
    "console",
    "engine",
    "publisher",
    "ui",
    "vidget_config",
    "_is_remote_publish_target",
]
