"""``vidget formats`` command."""

from __future__ import annotations

import json
import sys

import typer

from jre_vidget import cli_common as cc


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
            info = cc.engine.fetch_info(url)
        else:
            with cc.ui.spinner("Fetching video info…"):
                info = cc.engine.fetch_info(url)
    except cc.engine.EngineError as e:
        if json_output:
            sys.stderr.write(f"could not fetch info: {e}\n")
        else:
            cc.ui.print_error("Could not fetch info", str(e))
        raise typer.Exit(code=1) from e

    if json_output:
        typer.echo(json.dumps(info.model_dump(mode="json"), default=str))
    else:
        cc.ui.print_video_info(info)
        cc.ui.print_formats_table(info)
