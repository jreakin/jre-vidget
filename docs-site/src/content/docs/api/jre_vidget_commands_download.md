---
title: jre_vidget.commands.download
description: "vidget download command."
---


``vidget download`` command.


#### load\_video\_info\_for\_publish

```python
def load_video_info_for_publish(url: str, *,
                                json_output: bool) -> VideoInfo | None
```

Fetch `VideoInfo` for publish title fallback; logs and returns ``None`` on engine errors.


#### run\_engine\_download

```python
def run_engine_download(dl_cfg: DownloadConfig, *,
                        json_output: bool) -> DownloadResult
```

Run `engine.download` with optional Rich progress (disabled for ``--json``).


#### emit\_download\_json\_stdout

```python
def emit_download_json_stdout(result: DownloadResult,
                              pub_result: PublishResult | None) -> None
```

Emit the machine-readable download (and optional publish) payload.


#### download

```python
def download(
        url: str = typer.Argument(..., help="Video page URL to download"),
        quality: Quality | None = typer.Option(
            None,
            "--quality",
            "-q",
            help="best | 1080p | 720p | 480p | audio",
        ),
        out_format: OutputFormat | None = typer.Option(
            None,
            "--format",
            "-f",
            help="mp4 | mp3 | mkv | m4a | …",
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output directory",
        ),
        subs: bool | None = typer.Option(
            None,
            "--subs/--no-subs",
            help="Download subtitles (default: saved config).",
        ),
        publish_flag: bool = typer.Option(
            False,
            "--publish",
            help="Upload to YouTube after download.",
        ),
        pub_title: str | None = typer.Option(
            None,
            "--title",
            help="YouTube title (default: scraped title).",
        ),
        pub_description: str = typer.Option(
            "",
            "--description",
            help="YouTube description.",
        ),
        pub_privacy: PrivacyStatus = typer.Option(
            PrivacyStatus.PUBLIC,
            "--privacy",
            help="YouTube privacy: public, unlisted, or private.",
        ),
        pub_remove: bool = typer.Option(
            False,
            "--remove",
            help="Delete local file after upload.",
        ),
        json_output: bool = typer.
    Option(
        False,
        "--json",
        help=
        "Emit only JSON on stdout (download result; includes publish when --publish).",
    )) -> None
```

Download a single video.

