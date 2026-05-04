"""``vidget preview`` command."""

from __future__ import annotations

import json

import typer

from jre_vidget import cli_common as cc
from jre_vidget.models import DownloadError


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
        meta = cc.engine.preview(url)
    except DownloadError as exc:
        cc.ui.print_error("Preview failed", str(exc))
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(meta.model_dump(mode="json"), indent=2))
        return

    cc.ui.print_preview(meta)
