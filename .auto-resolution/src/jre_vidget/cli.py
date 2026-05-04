<<<<<<< New base: Add GitNexus docs, Typer CLI, and Rich UI
"""Typer CLI — delegates to engine; display via Rich in ui.py."""

from __future__ import annotations

from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Literal, TypeVar, cast

||||||| Common ancestor
=======
"""Typer CLI — delegates to engine; display via Rich (console / tables)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, TypeVar, cast

>>>>>>> Current commit: Add GitNexus docs, Typer CLI, and Rich UI
import typer

from jre_vidget import auth, checks, engine, models, publisher, ui
from jre_vidget.auth import AuthError
from jre_vidget.models import (
    AppConfig,
    BatchJob,
    DownloadConfig,
    DownloadStatus,
    OutputFormat,
    PublishConfig,
    Quality,
)
from jre_vidget.publisher import PublishError

PrivacyStatus = Literal["public", "unlisted", "private"]
_VALID_PRIVACY = frozenset({"public", "unlisted", "private"})

console = Console()


def _parse_privacy(value: str) -> PrivacyStatus:
    if value not in _VALID_PRIVACY:
        raise typer.BadParameter("privacy must be public, unlisted, or private")
    return cast(PrivacyStatus, value)


from jre_vidget import auth, checks, engine, models, publisher, ui
from jre_vidget.auth import AuthError
from jre_vidget.models import (
    AppConfig,
    BatchJob,
    DownloadConfig,
    DownloadStatus,
    OutputFormat,
    PublishConfig,
    Quality,
)
from jre_vidget.publisher import PublishError

PrivacyStatus = Literal["public", "unlisted", "private"]
_VALID_PRIVACY = frozenset({"public", "unlisted", "private"})

console = Console()


def _parse_privacy(value: str) -> PrivacyStatus:
    if value not in _VALID_PRIVACY:
        raise typer.BadParameter("privacy must be public, unlisted, or private")
    return cast(PrivacyStatus, value)


app = typer.Typer(
    name="vidget",
    help="🎬  Download & convert videos from 1000+ sites.",
    add_completion=False,
    no_args_is_help=True,
)
<<<<<<< New base: Add GitNexus docs, Typer CLI, and Rich UI
config_app = typer.Typer(help="View or edit default settings.")
app.add_typer(config_app, name="config")

auth_app = typer.Typer(help="Manage YouTube account connection.")
app.add_typer(auth_app, name="auth")


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
    if ctx.invoked_subcommand != "config":
        checks.check_dependencies()


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
    if ctx.invoked_subcommand != "config":
        checks.check_dependencies()


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


def _validate_output(path: Path) -> Path:
    """Ensure the path exists or can be created, and is writable."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        ui.print_error(f"Cannot write to {path}", "Check directory permissions.")
        raise typer.Exit(code=1) from None
    return path
||||||| Common ancestor
console = Console()
=======
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
>>>>>>> Current commit: Add GitNexus docs, Typer CLI, and Rich UI


@app.command()
<<<<<<< New base: Add GitNexus docs, Typer CLI, and Rich UI
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
    pub_privacy: str = typer.Option(
        "public",
        "--privacy",
        help="public | unlisted | private",
    ),
    pub_remove: bool = typer.Option(
        False,
        "--remove",
        help="Delete local file after upload.",
    ),
) -> None:
||||||| Common ancestor
def download(url: str = typer.Argument(..., help="Video URL to download")) -> None:
=======
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
>>>>>>> Current commit: Add GitNexus docs, Typer CLI, and Rich UI
    """Download a single video."""
<<<<<<< New base: Add GitNexus docs, Typer CLI, and Rich UI
    cfg = AppConfig.load()
    resolved_quality = _resolve(quality, cfg.quality)
    resolved_format = _resolve(out_format, cfg.format)
    resolved_output = _validate_output(_resolve(output, cfg.output_dir))
    resolved_subs = subs if subs else cfg.subtitles

    video_info = None
    if publish_flag:
        try:
            video_info = engine.fetch_info(url)
        except engine.EngineError as e:
            console.print(f"[yellow]Warning:[/yellow] Could not fetch video info: {e}")
            video_info = None

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
    except KeyboardInterrupt:
        ui.print_error("Download cancelled.", "Ctrl-C received.")
        raise typer.Exit(code=130) from None
    except engine.EngineError as e:
        ui.print_error("Error", str(e))
        raise typer.Exit(code=1) from e

    ui.print_result(result)
    if result.status != DownloadStatus.SUCCESS:
        raise typer.Exit(code=1)

    if publish_flag and result.filepath:
        pub_privacy_parsed = _parse_privacy(pub_privacy)
        resolved_title = pub_title or (video_info.title if video_info else url)
        publish_config = PublishConfig(
            filepath=result.filepath,
            title=resolved_title,
            description=pub_description,
            privacy=pub_privacy_parsed,
            remove_after_upload=pub_remove,
        )

        try:
            with console.status("Uploading to YouTube…"):
                pub_result = publisher.upload(publish_config, cfg.auth)
        except AuthError as e:
            console.print(f"[red]YouTube auth error:[/red] {e}")
            raise typer.Exit(code=3) from e
        except PublishError as e:
            console.print(f"[red]YouTube upload failed:[/red] {e}")
            raise typer.Exit(code=1) from e

        console.print(f"[green]✓[/green] Published: {pub_result.url}")
        if pub_result.removed_local_file:
            console.print(f"  Local file removed: {result.filepath}")


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
    out_dir = _validate_output(_resolve(output, cfg.output_dir))
    base = DownloadConfig(
        url="",
        quality=_resolve(quality, cfg.quality),
        format=_resolve(out_format, cfg.format),
        output_dir=out_dir,
        subtitles=subs if subs else cfg.subtitles,
    )
    job = BatchJob(urls=urls, config=base)
    hook, progress_ctx = ui.make_progress_hook()
    try:
        with progress_ctx:
            engine.download_batch(job, progress_hook=hook, on_result=ui.print_result)
    except KeyboardInterrupt:
        ui.print_error("Download cancelled.", "Ctrl-C received.")
        raise typer.Exit(code=130) from None

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


@config_app.command("reset")
def config_reset(
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation prompt"),
) -> None:
    """Reset all settings to defaults."""
    if not yes and not typer.confirm("Reset all config to defaults?", default=False):
        raise typer.Exit(code=0)

    if models.CONFIG_PATH.exists():
        models.CONFIG_PATH.unlink()

    ui.print_success("✅ Config reset.")


@auth_app.command("login")
def auth_login() -> None:
    """Connect your YouTube account via browser OAuth."""
    cfg = AppConfig.load()

    client_id = cfg.auth.client_id or typer.prompt("Google OAuth Client ID")
    client_secret = cfg.auth.client_secret or typer.prompt(
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
    if cfg.auth.refresh_token:
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


@app.command()
def publish(
    filepath: Path = typer.Argument(..., help="Path to the local video file to upload."),
    title: str | None = typer.Option(None, "--title", help="Video title (default: filename)."),
    description: str = typer.Option("", "--description", help="Video description."),
    privacy: str = typer.Option("public", "--privacy", help="public | unlisted | private"),
    remove: bool = typer.Option(
        False, "--remove", help="Delete local file after successful upload."
    ),
) -> None:
    """Upload a local video file to your YouTube channel."""
    cfg = AppConfig.load()

    if not filepath.exists():
        console.print(f"[red]File not found:[/red] {filepath}")
        raise typer.Exit(code=1)

    resolved_title = title or filepath.stem
    privacy_parsed = _parse_privacy(privacy)

    publish_config = PublishConfig(
        filepath=filepath,
        title=resolved_title,
        description=description,
        privacy=privacy_parsed,
        remove_after_upload=remove,
    )
||||||| Common ancestor
    console.print(f"[bold green]Phase 1 stub:[/] would download {url}")
=======
    cfg = AppConfig.load()
    resolved_quality = _resolve(quality, cfg.quality)
    resolved_format = _resolve(out_format, cfg.format)
    resolved_output = _validate_output(_resolve(output, cfg.output_dir))
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
    except KeyboardInterrupt:
        ui.print_error("Download cancelled.", "Ctrl-C received.")
        raise typer.Exit(code=130) from None
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
    out_dir = _validate_output(_resolve(output, cfg.output_dir))
    base = DownloadConfig(
        url="",
        quality=_resolve(quality, cfg.quality),
        format=_resolve(out_format, cfg.format),
        output_dir=out_dir,
        subtitles=subs if subs else cfg.subtitles,
    )
    job = BatchJob(urls=urls, config=base)
    hook, progress_ctx = ui.make_progress_hook()
    try:
        with progress_ctx:
            engine.download_batch(job, progress_hook=hook, on_result=ui.print_result)
    except KeyboardInterrupt:
        ui.print_error("Download cancelled.", "Ctrl-C received.")
        raise typer.Exit(code=130) from None

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
>>>>>>> Current commit: Add GitNexus docs, Typer CLI, and Rich UI

<<<<<<< New base: Add GitNexus docs, Typer CLI, and Rich UI
    try:
        with console.status("Uploading to YouTube…"):
            result = publisher.upload(publish_config, cfg.auth)
    except AuthError as e:
        console.print(f"[red]Auth error:[/red] {e}")
        raise typer.Exit(code=3) from e
    except PublishError as e:
        console.print(f"[red]Upload failed:[/red] {e}")
        raise typer.Exit(code=1) from e
||||||| Common ancestor
=======
    if not changed:
        ui.print_warning("No options given; nothing to update.")
        raise typer.Exit(code=0)
>>>>>>> Current commit: Add GitNexus docs, Typer CLI, and Rich UI

<<<<<<< New base: Add GitNexus docs, Typer CLI, and Rich UI
    console.print(f"[green]✓[/green] Published: {result.url}")
    if result.removed_local_file:
        console.print(f"  Local file removed: {filepath}")
||||||| Common ancestor
if __name__ == "__main__":
    app()
=======
    cfg.save()
    ui.print_success("Updated: " + ", ".join(changed))
>>>>>>> Current commit: Add GitNexus docs, Typer CLI, and Rich UI
