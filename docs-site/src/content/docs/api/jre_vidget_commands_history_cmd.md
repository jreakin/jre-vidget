---
title: jre_vidget.commands.history_cmd
description: "vidget history subcommands."
---


``vidget history`` subcommands.


#### history\_append

```python
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
        json_output: bool = typer.
    Option(
        False,
        "--json",
        help=
        "Print a single JSON object on stdout (ok + record, or ok false + error).",
    )) -> None
```

Prepend one upload record and ensure ``schemaVersion`` is set.

