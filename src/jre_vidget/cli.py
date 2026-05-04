"""Typer CLI — thin entry: mounts command groups and top-level commands."""

from __future__ import annotations

from importlib.metadata import version as pkg_version

import typer

# Re-export: ``jre_vidget.cli.engine`` matches what commands use via ``cli_common`` (tests patch here).
from jre_vidget import auth, checks, engine, publisher, ui
from jre_vidget.cli_common import (
    PublishOptions,
    _dispatch_publish_workflow,
    _ensure_cli_logging,
    _is_headless,
    _publish_config_for_downloaded_file,
    _resolve_download_config,
    _resolve_publish_title_for_download,
)
from jre_vidget.commands import (
    auth_cmd,
    batch,
    config_cmd,
    download,
    formats,
    history_cmd,
    preview,
    publish_cmd,
)

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


app.command()(download.download)
app.command()(batch.batch)
app.command()(formats.formats)
app.command()(preview.preview)
app.command()(publish_cmd.publish)

config_app.command("show")(config_cmd.config_show)
config_app.command("set")(config_cmd.config_set)
config_app.command("reset")(config_cmd.config_reset)

auth_app.command("login")(auth_cmd.auth_login)
auth_app.command("status")(auth_cmd.auth_status)
auth_app.command("logout")(auth_cmd.auth_logout)

history_app.command("append")(history_cmd.history_append)

__all__ = [
    "PublishOptions",
    "_dispatch_publish_workflow",
    "_is_headless",
    "_publish_config_for_downloaded_file",
    "_resolve_download_config",
    "_resolve_publish_title_for_download",
    "app",
    "auth",
    "checks",
    "engine",
    "main",
    "publisher",
    "ui",
]
