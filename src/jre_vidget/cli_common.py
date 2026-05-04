"""Shared CLI helpers; command modules import engine/auth/etc. from here for one patch target."""

from __future__ import annotations

import json
import logging
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import typer
from rich.console import Console

from jre_vidget import auth, checks, engine, publisher, ui
from jre_vidget import config as vidget_config
from jre_vidget.auth import AuthError
from jre_vidget.github_workflow import dispatch_publish_workflow
from jre_vidget.models import (
    AppConfig,
    AuthConfig,
    DownloadConfig,
    DownloadResult,
    OutputFormat,
    PrivacyStatus,
    PublishConfig,
    PublishResult,
    Quality,
    VideoInfo,
)
from jre_vidget.publish_flow import (
    PublishOptions,
    publish_config_for_downloaded_file,
    resolve_publish_title_for_download,
)
from jre_vidget.publisher import PublishError

console = Console(stderr=True)


@contextmanager
def progress_hook_session(*, json_output: bool) -> Iterator[engine.ProgressHook | None]:
    """
    Yield a Rich-backed yt-dlp progress hook, or ``None`` when ``json_output`` disables UI.

    When non-JSON, the Rich ``Progress`` context stays active for the whole ``with`` block.
    Callers must run the yt-dlp work (e.g. ``engine.download`` / ``engine.download_batch``)
    inside this ``with`` so the bar stays mounted for the full operation.
    """
    if json_output:
        yield None
        return
    hook, progress_ctx = ui.make_progress_hook()
    with progress_ctx:
        yield hook


# Set True after the first ``ensure_cli_logging()`` attempt (mirrors one-shot ``basicConfig`` semantics).
_vidget_cli_logging_initialized = False


class _JsonLineFormatter(logging.Formatter):
    """One JSON object per log line (stdlib only; enable via ``VIDGET_LOG_FORMAT=json``)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def _log_level_from_env() -> int:
    """Resolve ``VIDGET_LOG_LEVEL`` to a ``logging`` module level constant."""
    raw = os.getenv("VIDGET_LOG_LEVEL", "WARNING").strip()
    name = raw.upper() if raw else "WARNING"
    candidate = getattr(logging, name, logging.WARNING)
    return candidate if isinstance(candidate, int) else logging.WARNING


def ensure_cli_logging() -> None:
    """Configure root logging once per process from ``VIDGET_LOG_LEVEL`` and optional ``VIDGET_LOG_FORMAT``."""
    global _vidget_cli_logging_initialized
    if _vidget_cli_logging_initialized:
        return
    _vidget_cli_logging_initialized = True
    root = logging.getLogger()
    if root.handlers:
        return
    level = _log_level_from_env()
    handler = logging.StreamHandler(sys.stderr)
    fmt = os.getenv("VIDGET_LOG_FORMAT", "").strip().lower()
    if fmt == "json":
        handler.setFormatter(_JsonLineFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    root.addHandler(handler)
    root.setLevel(level)


def is_headless() -> bool:
    """True when stdin is not a TTY (pipelines, CI, Typer CliRunner)."""
    return not sys.stdin.isatty()


def parse_privacy(value: str) -> PrivacyStatus:
    """Validate CLI / workflow privacy string → :class:`PrivacyStatus` with a stable error message."""
    try:
        return PrivacyStatus(value)
    except ValueError:
        raise typer.BadParameter("privacy must be public, unlisted, or private") from None


def resolve_download_config(
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
    resolved_output = validate_output(output if output is not None else cfg.output_dir)
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


def read_batch_urls(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    urls: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        urls.append(s)
    return urls


def is_remote_publish_target(target: str) -> bool:
    t = target.strip()
    return t.startswith(("http://", "https://"))


def validate_output(path: Path) -> Path:
    """Ensure the path exists or can be created, and is writable."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        ui.print_error(f"Cannot write to {path}", "Check directory permissions.")
        raise typer.Exit(code=1) from None
    return path


def youtube_upload_or_exit(
    publish_config: PublishConfig,
    auth_config: AuthConfig,
    *,
    json_output: bool = False,
) -> PublishResult:
    """Run resumable upload with a Rich spinner; map auth/upload failures to ``typer.Exit``.

    When ``json_output`` is True, human-readable error lines are written to stderr as plain text.
    If ``VIDGET_LOG_FORMAT=json`` is also set, JSON log lines may appear on the same stream; do not
    assume stderr is only JSON.
    """
    try:
        with console.status("Uploading to YouTube…"):
            return publisher.upload(publish_config, auth_config)
    except AuthError as e:
        if json_output:
            sys.stderr.write(f"publish auth error: {e}\n")
        else:
            console.print(f"[red]YouTube auth error:[/red] {e}")
        raise typer.Exit(code=3) from e
    except PublishError as e:
        if json_output:
            sys.stderr.write(f"publish error: {e}\n")
        else:
            console.print(f"[red]YouTube upload failed:[/red] {e}")
        raise typer.Exit(code=1) from e


def require_interactive_confirm(
    *,
    yes: bool,
    prompt: str,
    headless_denial_message: str,
    headless_exit_code: int = 2,
    decline_rich_message: str | None = None,
    confirm_default: bool = False,
) -> None:
    """Unless ``yes`` is set, require a TTY and a positive ``typer.confirm`` (else exit)."""
    if yes:
        return
    if is_headless():
        console.print(f"[red]{headless_denial_message}[/red]")
        raise typer.Exit(code=headless_exit_code)
    if not typer.confirm(prompt, default=confirm_default):
        if decline_rich_message:
            console.print(decline_rich_message)
        raise typer.Exit(code=0)


def publish_after_download(
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
    publish_config = publish_config_for_downloaded_file(
        fp,
        options,
        video_info=video_info,
        url=url,
    )
    return youtube_upload_or_exit(publish_config, cfg.auth, json_output=json_output)


__all__ = [
    "AuthError",
    "PublishError",
    "PublishOptions",
    "auth",
    "checks",
    "console",
    "dispatch_publish_workflow",
    "ensure_cli_logging",
    "engine",
    "is_headless",
    "is_remote_publish_target",
    "parse_privacy",
    "progress_hook_session",
    "publish_after_download",
    "publish_config_for_downloaded_file",
    "publisher",
    "read_batch_urls",
    "require_interactive_confirm",
    "resolve_download_config",
    "resolve_publish_title_for_download",
    "ui",
    "validate_output",
    "vidget_config",
    "youtube_upload_or_exit",
]
