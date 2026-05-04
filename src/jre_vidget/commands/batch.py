"""``vidget batch`` command."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from jre_vidget import cli_common as cc
from jre_vidget.models import AppConfig, BatchJob, OutputFormat, Quality


def batch(
    file: Path = typer.Argument(..., help="Text file with one URL per line"),
    quality: Quality | None = typer.Option(None, "--quality", "-q"),
    out_format: OutputFormat | None = typer.Option(None, "--format", "-f"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    subs: bool | None = typer.Option(
        None,
        "--subs/--no-subs",
        help="Download subtitles (default: saved config).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit only JSON on stdout (list of download results).",
    ),
) -> None:
    """Download all URLs listed in a text file (one per line)."""
    if not file.is_file():
        cc.ui.print_error("File not found", str(file))
        raise typer.Exit(code=1)

    urls = cc._read_batch_urls(file)
    if not json_output:
        cc.ui.print_batch_intro(len(urls))

    cfg = AppConfig.load()
    base = cc._resolve_download_config(
        cfg,
        quality,
        out_format,
        output,
        subs,
        "",
        max_concurrent=cfg.max_concurrent,
    )
    job = BatchJob(urls=urls, config=base)
    try:
        if json_output:
            cc.engine.download_batch(job, progress_hook=None, on_result=None)
        else:
            hook, progress_ctx = cc.ui.make_progress_hook()
            with progress_ctx:
                cc.engine.download_batch(job, progress_hook=hook, on_result=cc.ui.print_result)
    except KeyboardInterrupt:
        cc.ui.print_error("Download cancelled.", "Ctrl-C received.")
        raise typer.Exit(code=130) from None

    if json_output:
        rows = [r.model_dump(mode="json") for r in job.results]
        typer.echo(json.dumps(rows, default=str))
    else:
        cc.ui.print_batch_summary(job)
