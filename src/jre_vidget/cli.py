"""Typer CLI — delegates to engine; display via Rich in ui.py."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import TypeVar

import typer
from rich.console import Console

from jre_vidget import auth, checks, engine, history, publisher, ui
from jre_vidget import config as vidget_config
from jre_vidget.auth import AuthError
from jre_vidget.models import (
    AppConfig,
    BatchJob,
    DownloadConfig,
    DownloadError,
    DownloadResult,
    DownloadStatus,
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


app = typer.Typer(
    name="vidget",
    help="🎬  Download & convert videos from 1000+ sites.",
    add_completion=False,
    no_args_is_help=True,
)
config_app = typer.Typer(help="View or edit default settings.")
app.add_typer(config_app, name="config")

auth_app = typer.Typer(help="Manage YouTube account connection.")
app.add_typer(auth_app, name="auth")

history_app = typer.Typer(help="Manage repo upload history (uploads.json).")
app.add_typer(history_app, name="history")


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"vidget {pkg_version('jre-vidget')}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    _version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Global options; runs before every subcommand."""
    _ensure_cli_logging()
    if ctx.invoked_subcommand not in ("config", "history"):
        checks.check_dependencies()


T = TypeVar("T")


def _resolve(value: T | None, default: T) -> T:
    """Return value if set, otherwise fall back to default."""
    return value if value is not None else default


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
    resolved_quality = _resolve(quality, cfg.quality)
    resolved_format = _resolve(out_format, cfg.format)
    resolved_output = _validate_output(_resolve(output, cfg.output_dir))
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


def _publish_after_download(
    cfg: AppConfig,
    result: DownloadResult,
    *,
    pub_title: str | None,
    pub_description: str,
    pub_privacy: PrivacyStatus,
    pub_remove: bool,
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
    resolved_title = pub_title or (video_info.title if video_info else url)
    publish_config = PublishConfig(
        filepath=fp,
        title=resolved_title,
        description=pub_description,
        privacy=pub_privacy,
        remove_after_upload=pub_remove,
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
        help="public | unlisted | private",
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
    cfg = AppConfig.load()
    dl_cfg = _resolve_download_config(cfg, quality, out_format, output, subs, url)

    video_info = None
    if publish_flag:
        try:
            video_info = engine.fetch_info(url)
        except engine.EngineError as e:
            if json_output:
                sys.stderr.write(f"warning: could not fetch video info: {e}\n")
            else:
                console.print(f"[yellow]Warning:[/yellow] Could not fetch video info: {e}")
            video_info = None

    try:
        if json_output:
            result = engine.download(dl_cfg, progress_hook=None)
        else:
            hook, progress_ctx = ui.make_progress_hook()
            with progress_ctx:
                result = engine.download(dl_cfg, progress_hook=hook)
    except KeyboardInterrupt:
        ui.print_error("Download cancelled.", "Ctrl-C received.")
        raise typer.Exit(code=130) from None
    except engine.EngineError as e:
        if json_output:
            sys.stderr.write(f"download error: {e}\n")
        else:
            ui.print_error("Error", str(e))
        raise typer.Exit(code=1) from e

    if not json_output:
        ui.print_result(result)

    if result.status != DownloadStatus.SUCCESS:
        if json_output:
            typer.echo(json.dumps({"download": result.model_dump(mode="json")}, default=str))
        raise typer.Exit(code=1)

    pub_result: PublishResult | None = None
    if publish_flag:
        pub_result = _publish_after_download(
            cfg,
            result,
            pub_title=pub_title,
            pub_description=pub_description,
            pub_privacy=pub_privacy,
            pub_remove=pub_remove,
            video_info=video_info,
            url=url,
            json_output=json_output,
        )

    if json_output:
        out: dict[str, object] = {"download": result.model_dump(mode="json")}
        if pub_result is not None:
            out["publish"] = pub_result.model_dump(mode="json")
        typer.echo(json.dumps(out, default=str))
    elif pub_result is not None:
        console.print(f"[green]✓[/green] Published: {pub_result.url}")
        if pub_result.removed_local_file:
            console.print(f"  Local file removed: {result.filepath}")


@app.command()
def batch(
    file: Path = typer.Argument(..., help="Text file with one URL per line"),
    quality: Quality | None = typer.Option(None, "--quality", "-q"),
    out_format: OutputFormat | None = typer.Option(None, "--format", "-f"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    subs: bool | None = typer.Option(
        None,
        "--subs/--no-subs",
        help="Download subtitles (default: saved config).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit only JSON on stdout (list of download results).",
    ),
) -> None:
    """Download all URLs listed in a text file (one per line)."""
    if not file.is_file():
        ui.print_error("File not found", str(file))
        raise typer.Exit(code=1)

    urls = _read_batch_urls(file)
    if not json_output:
        ui.print_batch_intro(len(urls))

    cfg = AppConfig.load()
    base = _resolve_download_config(
        cfg,
        quality,
        out_format,
        output,
        subs,
        "",
        max_concurrent=cfg.max_concurrent,
    )
    job = BatchJob(urls=urls, config=base)
    try:
        if json_output:
            engine.download_batch(job, progress_hook=None, on_result=None)
        else:
            hook, progress_ctx = ui.make_progress_hook()
            with progress_ctx:
                engine.download_batch(job, progress_hook=hook, on_result=ui.print_result)
    except KeyboardInterrupt:
        ui.print_error("Download cancelled.", "Ctrl-C received.")
        raise typer.Exit(code=130) from None

    if json_output:
        rows = [r.model_dump(mode="json") for r in job.results]
        typer.echo(json.dumps(rows, default=str))
    else:
        ui.print_batch_summary(job)


@app.command()
def formats(
    url: str = typer.Argument(..., help="Video page URL to inspect"),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit only JSON on stdout (VideoInfo).",
    ),
) -> None:
    """List available formats for a URL."""
    try:
        if json_output:
            info = engine.fetch_info(url)
        else:
            with ui.spinner("Fetching video info…"):
                info = engine.fetch_info(url)
    except engine.EngineError as e:
        if json_output:
            sys.stderr.write(f"could not fetch info: {e}\n")
        else:
            ui.print_error("Could not fetch info", str(e))
        raise typer.Exit(code=1) from e

    if json_output:
        typer.echo(json.dumps(info.model_dump(mode="json"), default=str))
    else:
        ui.print_video_info(info)
        ui.print_formats_table(info)


@app.command()
def preview(
    url: str = typer.Argument(..., help="Video URL to preview"),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output JSON only on stdout (for scripting).",
    ),
) -> None:
    """Fetch and display video metadata without downloading."""
    try:
        meta = engine.preview(url)
    except DownloadError as exc:
        ui.print_error("Preview failed", str(exc))
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(meta.model_dump(mode="json"), indent=2))
        return

    ui.print_preview(meta)


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


@config_app.command("reset")
def config_reset(
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation prompt"),
) -> None:
    """Reset all settings to defaults."""
    if not yes:
        if _is_headless():
            console.print(
                "[red]Non-interactive mode: pass --yes to confirm resetting all config.[/red]",
            )
            raise typer.Exit(code=2)
        if not typer.confirm("Reset all config to defaults?", default=False):
            raise typer.Exit(code=0)

    if vidget_config.CONFIG_PATH.exists():
        vidget_config.CONFIG_PATH.unlink()

    ui.print_success("✅ Config reset.")


@auth_app.command("login")
def auth_login() -> None:
    """Connect your YouTube account via browser OAuth."""
    cfg = AppConfig.load()

    client_id = cfg.auth.client_id or typer.prompt("Google OAuth Client ID")
    stored_secret = cfg.auth.client_secret.get_secret_value() if cfg.auth.client_secret else None
    client_secret = stored_secret or typer.prompt(
        "Google OAuth Client Secret",
        hide_input=True,
    )

    try:
        auth_config = auth.login_browser(client_id, client_secret)
    except Exception as e:
        console.print(f"[red]Login failed:[/red] {e}")
        raise typer.Exit(code=1) from e

    cfg.auth = auth_config
    cfg.save()
    console.print("[green]✓[/green] YouTube connected successfully.")


@auth_app.command("status")
def auth_status() -> None:
    """Show YouTube connection status."""
    cfg = AppConfig.load()
    has_rt = bool(cfg.auth.refresh_token.get_secret_value() if cfg.auth.refresh_token else "")
    if has_rt:
        console.print("[green]✓[/green] YouTube  connected")
    else:
        console.print(
            "[yellow]✗[/yellow] YouTube  not connected — run [bold]vidget auth login[/bold]",
        )


@auth_app.command("logout")
def auth_logout() -> None:
    """Disconnect your YouTube account."""
    cfg = AppConfig.load()
    auth.logout(cfg)
    console.print("[green]✓[/green] YouTube disconnected.")


@history_app.command("append")
def history_append(
    video_id: str = typer.Option(
        ...,
        "--video-id",
        envvar="VIDEO_ID",
        help="YouTube video id (GitHub Actions sets VIDEO_ID).",
    ),
    title: str = typer.Option(
        "",
        "--title",
        envvar="INPUT_TITLE",
        help="Display title; empty uses 'untitled'.",
    ),
    source_url: str = typer.Option(
        ...,
        "--source-url",
        envvar="INPUT_URL",
        help="Original download / source URL.",
    ),
    privacy: str = typer.Option(
        ...,
        "--privacy",
        envvar="INPUT_PRIVACY",
        help="Privacy at upload time (public | unlisted | private).",
    ),
    run_id: str = typer.Option(
        ...,
        "--run-id",
        envvar="RUN_ID",
        help="Workflow run id for traceability.",
    ),
    file: Path = typer.Option(
        Path("uploads.json"),
        "--file",
        "-f",
        help="Path to uploads.json (repo root in CI).",
    ),
) -> None:
    """Prepend one upload record and ensure ``schemaVersion`` is set."""
    try:
        history.append_upload_record(
            file,
            video_id=video_id,
            title=title,
            source_url=source_url,
            privacy=privacy,
            run_id=run_id,
        )
    except (OSError, ValueError) as e:
        ui.print_error("Could not update upload history", str(e))
        raise typer.Exit(code=1) from e


@app.command()
def publish(
    target: str = typer.Argument(
        ...,
        help="Local video file path, or https:// URL to dispatch the Actions publish workflow.",
    ),
    title: str | None = typer.Option(
        None,
        "--title",
        "-t",
        help="Video title (default: filename for local upload, or scraped title for URL).",
    ),
    description: str | None = typer.Option(
        None,
        "--description",
        "-d",
        help="Video description (local upload default empty).",
    ),
    privacy: PrivacyStatus = typer.Option(
        PrivacyStatus.PUBLIC,
        "--privacy",
        help="public | unlisted | private",
    ),
    remove: bool = typer.Option(
        False,
        "--remove",
        help="Delete local file after upload (local) or set workflow remove flag (URL).",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation when dispatching the Actions workflow (URL only).",
    ),
) -> None:
    """Upload a local file to YouTube, or preview then dispatch Actions publish for a URL."""
    cfg = AppConfig.load()

    if _is_remote_publish_target(target):
        console.print("[bold cyan]Fetching metadata…[/bold cyan]")
        try:
            meta = engine.preview(target)
        except DownloadError as exc:
            ui.print_error("Preview failed — cannot confirm before upload", str(exc))
            raise typer.Exit(code=1) from exc

        if title is not None:
            meta = meta.model_copy(update={"title": title})
        if description is not None:
            meta = meta.model_copy(update={"description": description})

        ui.print_preview(meta)

        if not yes:
            if _is_headless():
                console.print(
                    "[red]Non-interactive mode: pass --yes to confirm publishing to YouTube.[/red]",
                )
                raise typer.Exit(code=2)
            if not typer.confirm("\nPublish this video to YouTube?", default=False):
                console.print("[yellow]Publish cancelled.[/yellow]")
                raise typer.Exit(code=0)

        try:
            _dispatch_publish_workflow(
                url=target,
                title=meta.title,
                description=meta.description,
                privacy=privacy,
                remove_after_upload=remove,
            )
        except RuntimeError as e:
            ui.print_error("Could not start publish workflow", str(e))
            raise typer.Exit(code=1) from e

        console.print(
            "[green]✓[/green] Publish workflow started. Check GitHub Actions for progress."
        )
        return

    filepath = Path(target).expanduser()
    if not filepath.exists():
        console.print(f"[red]File not found:[/red] {filepath}")
        raise typer.Exit(code=1)

    resolved_title = title or filepath.stem
    desc = description if description is not None else ""

    publish_config = PublishConfig(
        filepath=filepath,
        title=resolved_title,
        description=desc,
        privacy=privacy,
        remove_after_upload=remove,
    )

    try:
        with console.status("Uploading to YouTube…"):
            result = publisher.upload(publish_config, cfg.auth)
    except AuthError as e:
        console.print(f"[red]Auth error:[/red] {e}")
        raise typer.Exit(code=3) from e
    except PublishError as e:
        console.print(f"[red]Upload failed:[/red] {e}")
        raise typer.Exit(code=1) from e

    console.print(f"[green]✓[/green] Published: {result.url}")
    if result.removed_local_file:
        console.print(f"  Local file removed: {filepath}")
