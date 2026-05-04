"""``vidget publish`` command."""

from __future__ import annotations

from pathlib import Path

import typer

from jre_vidget import cli_common as cc
from jre_vidget.models import AppConfig, DownloadError, PrivacyStatus, PublishConfig


def _run_remote_publish_flow(
    target: str,
    title: str | None,
    description: str | None,
    privacy: PrivacyStatus,
    remove: bool,
    *,
    yes: bool,
) -> None:
    """Preview URL metadata, confirm, then dispatch ``publish.yml`` via ``gh``."""
    cc.console.print("[bold cyan]Fetching metadata…[/bold cyan]")
    try:
        meta = cc.engine.preview(target)
    except DownloadError as exc:
        cc.ui.print_error("Preview failed — cannot confirm before upload", str(exc))
        raise typer.Exit(code=1) from exc

    if title is not None:
        meta = meta.model_copy(update={"title": title})
    if description is not None:
        meta = meta.model_copy(update={"description": description})

    cc.ui.print_preview(meta)

    cc.require_interactive_confirm(
        yes=yes,
        prompt="\nPublish this video to YouTube?",
        headless_denial_message=(
            "Non-interactive mode: pass --yes to confirm publishing to YouTube."
        ),
        headless_exit_code=2,
        decline_rich_message="[yellow]Publish cancelled.[/yellow]",
        confirm_default=False,
    )

    try:
        cc.dispatch_publish_workflow(
            url=target,
            title=meta.title,
            description=meta.description,
            privacy=privacy,
            remove_after_upload=remove,
        )
    except RuntimeError as e:
        cc.ui.print_error("Could not start publish workflow", str(e))
        raise typer.Exit(code=1) from e

    cc.console.print(
        "[green]✓[/green] Publish workflow started. Check GitHub Actions for progress."
    )


def _run_local_publish_flow(
    cfg: AppConfig,
    target: str,
    title: str | None,
    description: str | None,
    privacy: PrivacyStatus,
    remove: bool,
) -> None:
    """Upload a local file to YouTube via the Data API."""
    filepath = Path(target).expanduser()
    if not filepath.exists():
        cc.console.print(f"[red]File not found:[/red] {filepath}")
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

    result = cc.youtube_upload_or_exit(publish_config, cfg.auth, json_output=False)

    cc.console.print(f"[green]✓[/green] Published: {result.url}")
    if result.removed_local_file:
        cc.console.print(f"  Local file removed: {filepath}")


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
        help="YouTube privacy: public, unlisted, or private.",
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

    if cc.is_remote_publish_target(target):
        _run_remote_publish_flow(
            target,
            title,
            description,
            privacy,
            remove,
            yes=yes,
        )
        return

    _run_local_publish_flow(cfg, target, title, description, privacy, remove)
