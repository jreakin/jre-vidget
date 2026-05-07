---
title: jre_vidget.cli_common
description: "Shared CLI helpers; command modules import engine/auth/etc. from here for one patch target."
---


Shared CLI helpers; command modules import engine/auth/etc. from here for one patch target.


#### progress\_hook\_session

```python
@contextmanager
def progress_hook_session(
        *, json_output: bool) -> Iterator[engine.ProgressHook | None]
```

Yield a Rich-backed yt-dlp progress hook, or ``None`` when ``json_output`` disables UI.

When non-JSON, the Rich ``Progress`` context stays active for the whole ``with`` block.
Callers must run the yt-dlp work (e.g. ``engine.download`` / ``engine.download_batch``)
inside this ``with`` so the bar stays mounted for the full operation.


#### ensure\_cli\_logging

```python
def ensure_cli_logging() -> None
```

Configure root logging once per process from ``VIDGET_LOG_LEVEL`` and optional ``VIDGET_LOG_FORMAT``.


#### is\_headless

```python
def is_headless() -> bool
```

True when stdin is not a TTY (pipelines, CI, Typer CliRunner).


#### parse\_privacy

```python
def parse_privacy(value: str) -> PrivacyStatus
```

Validate CLI / workflow privacy string → `PrivacyStatus` with a stable error message.


#### resolve\_download\_config

```python
def resolve_download_config(
        cfg: AppConfig,
        quality: Quality | None,
        out_format: OutputFormat | None,
        output: Path | None,
        subs: bool | None,
        url: str,
        *,
        max_concurrent: int | None = None) -> DownloadConfig
```

Merge CLI overrides with saved defaults (``subs`` uses tri-state: None → config).


#### validate\_output

```python
def validate_output(path: Path) -> Path
```

Ensure the path exists or can be created, and is writable.


#### youtube\_upload\_or\_exit

```python
def youtube_upload_or_exit(publish_config: PublishConfig,
                           auth_config: AuthConfig,
                           *,
                           json_output: bool = False) -> PublishResult
```

Run resumable upload with a Rich spinner; map auth/upload failures to ``typer.Exit``.

When ``json_output`` is True, human-readable error lines are written to stderr as plain text.
If ``VIDGET_LOG_FORMAT=json`` is also set, JSON log lines may appear on the same stream; do not
assume stderr is only JSON.


#### require\_interactive\_confirm

```python
def require_interactive_confirm(*,
                                yes: bool,
                                prompt: str,
                                headless_denial_message: str,
                                headless_exit_code: int = 2,
                                decline_rich_message: str | None = None,
                                confirm_default: bool = False) -> None
```

Unless ``yes`` is set, require a TTY and a positive ``typer.confirm`` (else exit).


#### publish\_after\_download

```python
def publish_after_download(cfg: AppConfig,
                           result: DownloadResult,
                           *,
                           options: PublishOptions,
                           video_info: VideoInfo | None,
                           url: str,
                           json_output: bool = False) -> PublishResult
```

Upload the downloaded file to YouTube. Exits the process on auth or upload errors.

