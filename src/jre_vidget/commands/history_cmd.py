"""``vidget history`` subcommands."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from jre_vidget import cli_common as cc
from jre_vidget import history


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
        help="public | unlisted | private (validated before append).",
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
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print a single JSON object on stdout (ok + record, or ok false + error).",
    ),
) -> None:
    """Prepend one upload record and ensure ``schemaVersion`` is set."""
    privacy_status = cc.parse_privacy(privacy)
    try:
        record = history.append_upload_record(
            file,
            video_id=video_id,
            title=title,
            source_url=source_url,
            privacy=privacy_status.value,
            run_id=run_id,
        )
    except typer.Exit:
        raise
    except Exception as e:
        if json_output:
            typer.echo(
                json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False),
            )
        else:
            cc.ui.print_error("Could not update upload history", str(e))
        raise typer.Exit(code=1) from e
    else:
        if json_output:
            typer.echo(
                json.dumps(
                    {"ok": True, "record": record},
                    ensure_ascii=False,
                    default=str,
                ),
            )
