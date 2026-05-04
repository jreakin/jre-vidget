"""``vidget config`` subcommands."""

from __future__ import annotations

from pathlib import Path

import typer

from jre_vidget import cli_common as cc
from jre_vidget.models import AppConfig, OutputFormat, Quality


def config_show() -> None:
    """Print current saved configuration."""
    cfg = AppConfig.load()
    cc.ui.print_config(cfg)


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
        cc.ui.print_warning("No options given; nothing to update.")
        raise typer.Exit(code=0)

    cfg.save()
    cc.ui.print_success("Updated: " + ", ".join(changed))


def config_reset(
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation prompt"),
) -> None:
    """Reset all settings to defaults."""
    cc.require_interactive_confirm(
        yes=yes,
        prompt="Reset all config to defaults?",
        headless_denial_message="Non-interactive mode: pass --yes to confirm resetting all config.",
        headless_exit_code=2,
        decline_rich_message=None,
        confirm_default=False,
    )

    if cc.vidget_config.CONFIG_PATH.exists():
        cc.vidget_config.CONFIG_PATH.unlink()

    cc.ui.print_success("✅ Config reset.")
