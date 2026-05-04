# Phase 4 — Typer CLI Commands
# Version: 0.1.0
# Model: claude-sonnet-4-6
# Last Updated: 2026-05-03
# Maintainer: jreakin
# Status: Draft

---

## Goal
Wire up all CLI commands in `src/jre_vidget/cli.py` using Typer.
The CLI is the user-facing layer only — it delegates all work to `engine.py`
and all display to `ui.py` (which is stubbed for now; rich `print` calls are fine
until Phase 5 upgrades them).

---

## Prerequisites
Phases 1–3 complete. Engine and models tested and passing.

---

## Command surface

```
vidget <url> [OPTIONS]         # download a single video
vidget batch <file> [OPTIONS]  # download all URLs in a text file
vidget formats <url>           # list available formats for a URL
vidget config show             # print current config
vidget config set [OPTIONS]    # update stored defaults
```

---

## Deliverables

### `src/jre_vidget/cli.py`

#### Top-level app
```python
import typer
from rich.console import Console

app = typer.Typer(
    name="vidget",
    help="🎬  Download & convert videos from 1000+ sites.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()
config_app = typer.Typer(help="View or edit default settings.")
app.add_typer(config_app, name="config")
```

---

#### `vidget <url>` — download command (default)
```python
@app.command()
def download(
    url: str = typer.Argument(..., help="Video page URL to download"),
    quality: Quality = typer.Option(None, "--quality", "-q", help="best | 1080p | 720p | 480p | audio"),
    format:  OutputFormat = typer.Option(None, "--format",  "-f", help="mp4 | mp3 | mkv | m4a | …"),
    output:  Path | None  = typer.Option(None, "--output",  "-o", help="Output directory"),
    subs:    bool         = typer.Option(False, "--subs", help="Download subtitles if available"),
):
```

Implementation steps:
1. Load `AppConfig` — fill any `None` CLI args from stored config defaults
2. Build a `DownloadConfig` from the resolved options
3. Call `engine.download(config, progress_hook=ui.make_progress_hook())`
   (use a simple `print`-based hook for now; Phase 5 replaces this)
4. On `DownloadResult.status == SUCCESS` → print success message with filepath
5. On `FAILED` → print error and `raise typer.Exit(code=1)`

---

#### `vidget batch <file>` — batch download
```python
@app.command()
def batch(
    file:    Path         = typer.Argument(..., help="Text file with one URL per line"),
    quality: Quality      = typer.Option(None, "--quality", "-q"),
    format:  OutputFormat = typer.Option(None, "--format",  "-f"),
    output:  Path | None  = typer.Option(None, "--output",  "-o"),
    subs:    bool         = typer.Option(False, "--subs"),
):
```

Implementation steps:
1. Validate `file` exists — if not, print error and exit with code 1
2. Read lines, strip whitespace, skip blank lines and lines starting with `#`
3. Print `"Found N URLs"` summary
4. Load config, build a `DownloadConfig` (url="" placeholder)
5. Build a `BatchJob(urls=[...], config=config)`
6. Call `engine.download_batch(job, on_result=ui.print_result)`
7. Print final summary: completed / failed counts

---

#### `vidget formats <url>` — inspect available formats
```python
@app.command()
def formats(
    url: str = typer.Argument(..., help="Video page URL to inspect"),
):
```

Implementation steps:
1. Call `engine.fetch_info(url)` — show a spinner while fetching
2. Print video title, uploader, duration
3. Print a Rich `Table` with columns: Format ID | Resolution | FPS | Codec | Bitrate | Size
4. Only show `info.best_formats` (unique resolutions, best-first)
5. Separately show audio-only formats in a second table

---

#### `vidget config show`
```python
@config_app.command("show")
def config_show():
    """Print current saved configuration."""
```
Load `AppConfig` and print it as a Rich table with two columns: Setting | Value.

---

#### `vidget config set`
```python
@config_app.command("set")
def config_set(
    output:  Path | None  = typer.Option(None, "--output",  help="Default output directory"),
    quality: Quality      = typer.Option(None, "--quality", help="Default quality"),
    format:  OutputFormat = typer.Option(None, "--format",  help="Default output format"),
    subs:    bool | None  = typer.Option(None, "--subs/--no-subs"),
):
```

Implementation steps:
1. Load current config via `load_app_config()` from `jre_vidget.config`
2. Apply any non-None options over the loaded config
3. Call `save_app_config(cfg)`
4. Print confirmation of what changed

---

## Shared option defaults pattern
To avoid repeating `load_app_config()` in every command, use a shared
helper at the top of `cli.py`:

```python
def _resolve(value, default):
    """Return value if set, otherwise fall back to default."""
    return value if value is not None else default
```

Use it like:
```python
from jre_vidget.config import load_app_config

cfg = load_app_config()
quality = _resolve(quality, cfg.quality)
```

---

## Tests to write in `tests/test_cli.py`
Use `typer.testing.CliRunner`.

```python
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from jre_vidget.cli import app
from jre_vidget.models import DownloadResult, DownloadStatus
from pathlib import Path

runner = CliRunner()

def test_download_help():
    result = runner.invoke(app, ["download", "--help"])
    assert result.exit_code == 0
    assert "--quality" in result.output

def test_batch_missing_file_exits_1():
    result = runner.invoke(app, ["batch", "/nonexistent/urls.txt"])
    assert result.exit_code == 1

def test_config_show_runs():
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0

def test_download_success(tmp_path):
    fake_result = DownloadResult(
        url="https://x.com", status=DownloadStatus.SUCCESS,
        filepath=tmp_path / "video.mp4"
    )
    with patch("jre_vidget.cli.engine.download", return_value=fake_result):
        result = runner.invoke(app, ["download", "https://x.com",
                                     "--output", str(tmp_path)])
    assert result.exit_code == 0

def test_download_failure_exits_1(tmp_path):
    fake_result = DownloadResult(
        url="https://x.com", status=DownloadStatus.FAILED, error="404"
    )
    with patch("jre_vidget.cli.engine.download", return_value=fake_result):
        result = runner.invoke(app, ["download", "https://x.com"])
    assert result.exit_code == 1
```

---

## Acceptance criteria
- `vidget --help` shows all four commands
- `vidget download --help` shows all flags with descriptions
- `vidget config show` prints a table of defaults
- `vidget config set --quality 720p` persists the change (verify with `config show`)
- `pytest tests/test_cli.py` passes (5 tests, green)
- `vidget formats https://www.foxnews.com/video/6390070137112` prints a format table
