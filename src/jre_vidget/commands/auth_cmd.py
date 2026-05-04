"""``vidget auth`` subcommands."""

from __future__ import annotations

import typer

from jre_vidget import cli_common as cc
from jre_vidget.models import AppConfig


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
        auth_config = cc.auth.login_browser(client_id, client_secret)
    except KeyboardInterrupt:
        raise
    except Exception as e:  # noqa: BLE001 — OAuth/browser flows raise varied library types; always show a friendly CLI error.
        cc.console.print(f"[red]Login failed:[/red] {e}")
        raise typer.Exit(code=1) from e

    cfg.auth = auth_config
    cfg.save()
    cc.console.print("[green]✓[/green] YouTube connected successfully.")


def auth_status() -> None:
    """Show YouTube connection status."""
    cfg = AppConfig.load()
    has_rt = bool(cfg.auth.refresh_token.get_secret_value() if cfg.auth.refresh_token else "")
    if has_rt:
        cc.console.print("[green]✓[/green] YouTube  connected")
    else:
        cc.console.print(
            "[yellow]✗[/yellow] YouTube  not connected — run [bold]vidget auth login[/bold]",
        )


def auth_logout() -> None:
    """Disconnect your YouTube account."""
    cfg = AppConfig.load()
    cc.auth.logout(cfg)
    cc.console.print("[green]✓[/green] YouTube disconnected.")
