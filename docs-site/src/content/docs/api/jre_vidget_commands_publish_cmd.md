---
title: jre_vidget.commands.publish_cmd
description: "vidget publish command."
---


``vidget publish`` command.


#### publish

```python
def publish(
        target: str = typer.
    Argument(
        ...,
        help=
        "Local video file path, or https:// URL to dispatch the Actions publish workflow.",
    ),
        title: str
    | None = typer.Option(
        None,
        "--title",
        "-t",
        help=
        "Video title (default: filename for local upload, or scraped title for URL).",
    ),
        description: str | None = typer.Option(
            None,
            "--description",
            "-d",
            help="Video description (local upload default empty).",
        ),
        privacy: PrivacyStatus = typer.Option(
            PrivacyStatus.PUBLIC,
            "--privacy",
            help="YouTube privacy: public, unlisted, or private.",
        ),
        remove: bool = typer.
    Option(
        False,
        "--remove",
        help=
        "Delete local file after upload (local) or set workflow remove flag (URL).",
    ),
        yes: bool = typer.
    Option(
        False,
        "--yes",
        "-y",
        help=
        "Skip confirmation when dispatching the Actions workflow (URL only).",
    )) -> None
```

Upload a local file to YouTube, or preview then dispatch Actions publish for a URL.

