"""``vidget auth`` subcommands."""

from __future__ import annotations

import logging

import typer
from google.auth.exceptions import GoogleAuthError

from jre_vidget import cli_common as cc
from jre_vidget.config import load_app_config, save_app_config

_log = logging.getLogger(__name__)


def auth_login() -> None:
    """Connect your YouTube account via browser OAuth."""
    cfg = load_app_config()

    client_id = cfg.auth.client_id or typer.prompt("Google OAuth Client ID")
    stored_secret = cfg.auth.client_secret.get_secret_value() if cfg.auth.client_secret else None
    client_secret = stored_secret or typer.prompt(
        "Google OAuth Client Secret",
        hide_input=True,
    )

    try:
        auth_config = cc.auth.login_browser(client_id, client_secret)
    except KeyboardInterrupt:
        raise
    except Exception as e:  # noqa: BLE001 — OAuth/browser flows raise varied types
        if not isinstance(e, (GoogleAuthError, OSError, ValueError)):
            _log.exception("OAuth login failed")
        cc.console.print(f"[red]Login failed:[/red] {e}")
        raise typer.Exit(code=1) from e

    cfg.auth = auth_config
    save_app_config(cfg)
    cc.console.print("[green]✓[/green] YouTube connected successfully.")


def auth_status(
    strict: bool = typer.Option(
        False,
        "--strict",
        help=(
            "Exit with code 3 if client id, secret, and refresh token are missing or blank "
            "(env + config). Does not contact Google; upload still validates the token."
        ),
    ),
) -> None:
    """Show YouTube connection status (env vars ``VIDGET_*`` count the same as saved config)."""
    cfg = load_app_config()
    ready = cc.auth.publish_oauth_configured(cfg.auth)
    if ready:
        cc.console.print("[green]✓[/green] YouTube  connected")
    else:
        cc.console.print(
            "[yellow]✗[/yellow] YouTube  not connected — run [bold]vidget auth login[/bold]",
        )
    if strict and not ready:
        raise typer.Exit(code=3)


def auth_logout() -> None:
    """Disconnect your YouTube account."""
    cfg = load_app_config()
    cc.auth.logout(cfg)
    cc.console.print("[green]✓[/green] YouTube disconnected.")
