"""``vidget auth`` subcommands."""

from __future__ import annotations

import json
import logging

import typer
from google.auth.exceptions import GoogleAuthError

from jre_vidget import cli_common as cc
from jre_vidget.auth import AuthError
from jre_vidget.config import load_app_config, save_app_config

_log = logging.getLogger(__name__)


def auth_login(
    show_refresh_token: bool = typer.Option(
        False,
        "--show-refresh-token",
        help=(
            "After success, print the refresh token for copying into GitHub Actions secrets "
            "(GCLOUD_REFRESH_TOKEN or VIDGET_REFRESH_TOKEN). Avoid shared or logged terminals."
        ),
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="On success, print one JSON object to stdout with client_id and refresh_token only.",
    ),
) -> None:
    """Connect your YouTube account via browser OAuth."""
    cfg = load_app_config()

    client_id = cfg.auth.client_id or typer.prompt("Google OAuth Client ID")
    stored_secret = cfg.auth.client_secret.get_secret_value() if cfg.auth.client_secret else None
    client_secret = stored_secret or typer.prompt(
        "Google OAuth Client Secret",
        hide_input=True,
    )

    if not json_output:
        cc.console.print(
            "[dim]Opening Google sign-in in your default browser when possible. "
            "The terminal cannot navigate itself — after you approve access in the browser, "
            "Google sends that tab to localhost to complete the flow.[/dim]"
        )
    try:
        auth_config = cc.auth.login_browser(client_id, client_secret)
    except KeyboardInterrupt:
        raise
    except AuthError as e:
        cc.console.print(f"[red]Login failed:[/red] {e}")
        raise typer.Exit(code=1) from e
    except Exception as e:  # noqa: BLE001 — OAuth/browser flows raise varied types
        if not isinstance(e, (GoogleAuthError, OSError, ValueError)):
            _log.exception("OAuth login failed")
        cc.console.print(f"[red]Login failed:[/red] {e}")
        raise typer.Exit(code=1) from e

    cfg.auth = auth_config
    save_app_config(cfg)

    if json_output:
        rt = auth_config.refresh_token.get_secret_value() if auth_config.refresh_token else None
        print(
            json.dumps(
                {"client_id": auth_config.client_id, "refresh_token": rt},
                ensure_ascii=False,
            )
        )
        return

    cc.console.print("[green]✓[/green] YouTube connected successfully.")
    if show_refresh_token:
        assert auth_config.refresh_token is not None  # login_browser guarantees this
        rt = auth_config.refresh_token.get_secret_value()
        cc.console.print(
            "[yellow]Treat this like a password — it grants YouTube upload access.[/yellow]"
        )
        cc.console.print(
            "Set GitHub Actions secret [bold]GCLOUD_REFRESH_TOKEN[/bold] or "
            "[bold]VIDGET_REFRESH_TOKEN[/bold] to:"
        )
        cc.console.print(rt)


def auth_print_token(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print only JSON (client_id + refresh_token) to stdout.",
    ),
) -> None:
    """Print the resolved refresh token (saved config or env) — no browser; for GitHub Actions setup."""
    cfg = load_app_config()
    rt = cc.auth.read_refresh_token_merged(cfg.auth)
    cid = cc.auth.read_client_id_merged(cfg.auth)
    if not rt:
        cc.console.print(
            "[red]No refresh token found in ~/.vidget/config.json or environment "
            "(GCLOUD_REFRESH_TOKEN / VIDGET_REFRESH_TOKEN).[/red]"
        )
        raise typer.Exit(code=3)

    if json_output:
        print(json.dumps({"client_id": cid, "refresh_token": rt}, ensure_ascii=False))
        return

    cc.console.print(
        "[dim]GitHub Actions: add as secret GCLOUD_REFRESH_TOKEN or VIDGET_REFRESH_TOKEN.[/dim]"
    )
    cc.console.print(rt)


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
