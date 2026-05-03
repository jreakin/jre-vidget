# Phase 5 — Rich UI
# Version: 0.1.0
# Model: claude-sonnet-4-6
# Last Updated: 2026-05-03
# Maintainer: jreakin
# Status: Draft

---

## Goal
Upgrade all terminal output in `src/jre_vidget/ui.py` from plain `print` calls to
a polished Rich UI. Every `console.print` in `cli.py` should be replaced with a
call into `ui.py`. The engine never imports from `ui.py`.

---

## Prerequisites
Phases 1–4 complete. All CLI commands functional with basic print output.

---

## Deliverables

### `src/jre_vidget/ui.py`

---

#### Console singleton
```python
from rich.console import Console
console = Console()
```
All functions in this module use this shared `console` instance.

---

#### `spinner(message)` — context manager for any blocking operation
```python
from contextlib import contextmanager
from rich.status import Status

@contextmanager
def spinner(message: str):
    """Show a Rich spinner while a block executes."""
    with console.status(f"[bold cyan]{message}[/]", spinner="dots"):
        yield
```

Usage in `cli.py`:
```python
with ui.spinner("Fetching video info..."):
    info = engine.fetch_info(url)
```

---

#### `print_video_info(info: VideoInfo)` — header panel before download starts
Show a Rich `Panel` containing:
- **Title** (bold white)
- **Uploader** and **Upload date** on one line (dim)
- **Duration** (e.g. `5:05`)
- **URL** (dim, truncated to 60 chars)

Example output:
```
╭─────────────────────────────────────────────────────────╮
│  Karl Rove: Harris teases 2028 run…                     │
│  Fox News · Feb 27 2026  ·  5:05                        │
│  https://www.foxnews.com/video/639007013…               │
╰─────────────────────────────────────────────────────────╯
```

---

#### `print_formats_table(info: VideoInfo)` — display available formats

Print two Rich `Table`s:

**Video formats** (columns: #, Resolution, FPS, Codec, Bitrate, Size):
```
 Video Formats
┌───┬────────────┬───────┬───────────────┬──────────┬─────────┐
│ # │ Resolution │  FPS  │    Codec      │  Bitrate │  Size   │
├───┼────────────┼───────┼───────────────┼──────────┼─────────┤
│ 1 │ 1280x720   │ 30    │ avc1.4d001f   │ 1466 kbps│ ~56 MB  │
│ 2 │ 1024x576   │ 30    │ avc1.4d001f   │ 1061 kbps│ ~40 MB  │
│ 3 │  640x360   │ 30    │ avc1.4d001e   │  606 kbps│ ~23 MB  │
│ 4 │  384x216   │ 30    │ avc1.42000d   │  335 kbps│ ~13 MB  │
└───┴────────────┴───────┴───────────────┴──────────┴─────────┘
```

**Audio-only formats** (columns: #, Codec, Bitrate, Size):
Shown below the video table in a dimmer style.

---

#### `make_progress_hook()` — return a yt-dlp progress hook that drives a Rich Progress bar

```python
from rich.progress import (
    Progress, BarColumn, DownloadColumn,
    TransferSpeedColumn, TimeRemainingColumn, TextColumn,
)

def make_progress_hook():
    """
    Return a (hook_fn, progress_context) tuple.

    hook_fn is passed directly to yt-dlp's progress_hooks list.
    progress_context is a Rich Progress instance the caller should use
    as a context manager.

    Example usage in cli.py:
        hook, progress = ui.make_progress_hook()
        config = DownloadConfig(..., ...)
        with progress:
            result = engine.download(config, progress_hook=hook)
    """
```

The progress bar should show:
```
 Downloading ━━━━━━━━━━━━━━━━━━━━━━━━━━━━  45.2/100.0 MB  2.1 MB/s  eta 0:00:26
```

Implementation notes:
- On `status == "downloading"` → update the task's `completed` and `total`
- On `status == "finished"` → mark the task complete, print `"✅ Merging…"`
- On `status == "error"` → print a red error panel
- Use `total_bytes` if available, fall back to `total_bytes_estimate`

---

#### `print_result(result: DownloadResult)` — print outcome of one download
```python
def print_result(result: DownloadResult) -> None:
```
- `SUCCESS` → green checkmark, filename, duration taken
- `FAILED`  → red ✗ symbol, URL, error message in a dim panel
- `SKIPPED` → yellow ⚠ symbol, URL

---

#### `print_batch_summary(job: BatchJob)` — final summary after batch run

Print a Rich `Table` with one row per result:

```
 Batch Summary
┌──────────────────────────────────┬─────────┬───────────┐
│ URL                              │ Status  │ File      │
├──────────────────────────────────┼─────────┼───────────┤
│ https://foxnews.com/video/…      │ ✅ done │ karl….mp4 │
│ https://youtube.com/watch?v=…    │ ❌ fail │ 403 Error │
└──────────────────────────────────┴─────────┴───────────┘
  2 total  ·  1 completed  ·  1 failed
```

---

#### `print_config(config: AppConfig)` — show config as a styled table
```python
def print_config(config: AppConfig) -> None:
```
Two-column table: **Setting** | **Value** with cyan key names.

---

#### `print_error(message: str, detail: str | None = None)` — styled error panel
```python
def print_error(message: str, detail: str | None = None) -> None:
    console.print(Panel(
        f"[bold]{message}[/]\n{detail or ''}".strip(),
        title="[red]Error[/]",
        border_style="red",
    ))
```

---

## Wiring: update `cli.py`

Replace every plain `console.print(...)` in `cli.py` with the equivalent `ui.*` call:

| Before (Phase 4) | After (Phase 5) |
|------------------|----------------|
| `console.print(f"Fetching...")` | `with ui.spinner("Fetching video info…"):` |
| `console.print(table)` in `formats` | `ui.print_formats_table(info)` |
| `console.print("Done")` | `ui.print_result(result)` |
| `console.print("Summary")` | `ui.print_batch_summary(job)` |
| `console.print(config)` | `ui.print_config(config)` |
| Error prints | `ui.print_error(...)` |

---

## Acceptance criteria
- `vidget formats https://www.foxnews.com/video/6390070137112` shows a Rich table
- `vidget download <url>` shows a live progress bar during download
- `vidget batch urls.txt` shows per-URL results live and a summary table at the end
- `vidget config show` shows a styled two-column table
- All existing CLI tests still pass (`pytest tests/test_cli.py`)
- No `print()` builtins remain in `cli.py` or `ui.py` — only `console.print()`
