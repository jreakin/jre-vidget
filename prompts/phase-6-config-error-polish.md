# Phase 6 — Config, Error Handling & Polish

## Goal
Harden the tool for real-world use: robust error handling, retry logic,
dependency checks on startup, a `--version` flag, and a clean install story.
After this phase the tool should be shippable.

---

## Prerequisites
Phases 1–5 complete. Full UI rendering, all commands functional.

---

## Deliverables

### 1. Dependency pre-flight check — `src/jre_vidget/checks.py`

```python
def check_dependencies() -> None:
    """
    Verify that yt-dlp and ffmpeg are available before any command runs.
    Print a helpful install hint and exit(1) if either is missing.
    """
```

Rules:
- Check `yt_dlp` is importable — if not, print:
  ```
  ❌  yt-dlp not found. Install with: pip install yt-dlp
  ```
- Check `ffmpeg` is on `$PATH` (use `shutil.which("ffmpeg")`) — if not, print:
  ```
  ⚠️  ffmpeg not found — format conversion will not work.
     Install with: brew install ffmpeg
  ```
  (This is a warning, not a fatal error — downloading without conversion still works.)

Wire this into the Typer app using an `app.callback`:
```python
@app.callback()
def main(ctx: typer.Context):
    """Called before every command."""
    if ctx.invoked_subcommand != "config":
        checks.check_dependencies()
```

---

### 2. Retry logic — update `engine.py`

Add an optional `retries: int = 2` parameter to `download()`:

```python
def download(
    config: DownloadConfig,
    progress_hook: ProgressHook | None = None,
    retries: int = 2,
) -> DownloadResult:
```

On `DownloadError`, retry up to `retries` times with a 2-second back-off.
Log each retry attempt to the console:
```
⟳  Retry 1/2 for https://…
```
After exhausting retries, return `DownloadResult(status=FAILED, error=...)`.

Also add `retries` to `DownloadConfig` as an optional field:
```python
retries: int = Field(default=2, ge=0, le=5)
```

---

### 3. `--version` flag — update `cli.py`

```python
def version_callback(value: bool):
    if value:
        from importlib.metadata import version
        typer.echo(f"vidget {version('jre-vidget')}")
        raise typer.Exit()

@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(None, "--version", "-V",
                                  callback=version_callback, is_eager=True),
):
```

---

### 4. `vidget config reset` — new subcommand

```python
@config_app.command("reset")
def config_reset(
    confirm: bool = typer.Option(False, "--yes", help="Skip confirmation prompt"),
):
    """Reset all settings to defaults."""
```

If `--yes` not passed, prompt: `"Reset all config to defaults? [y/N]"`.
On confirm: delete `~/.vidget/config.json`, print `"✅ Config reset."`.

---

### 5. Graceful Ctrl-C handling — update `cli.py`

Wrap the body of `download` and `batch` commands:
```python
try:
    ...
except KeyboardInterrupt:
    ui.print_error("Download cancelled.", "Ctrl-C received.")
    raise typer.Exit(code=130)
```

---

### 6. `--output` path validation — update `cli.py`

After resolving `output_dir`, validate it:
```python
def _validate_output(path: Path) -> Path:
    """Ensure the path exists or can be created, and is writable."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        ui.print_error(f"Cannot write to {path}", "Check directory permissions.")
        raise typer.Exit(1)
    return path
```
Call this before building `DownloadConfig` in both `download` and `batch`.

---

### 7. `install.sh` — one-command setup script

Create `install.sh` in the project root:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "🎬  Installing vidget..."

# Python check
python3 -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'" \
  || { echo "❌  Python 3.11+ is required."; exit 1; }

# Install package
pip3 install -e ".[dev]" --quiet

# ffmpeg check
if ! command -v ffmpeg &>/dev/null; then
  echo "⚠️  ffmpeg not found. Install with: brew install ffmpeg"
else
  echo "✅  ffmpeg: $(ffmpeg -version 2>&1 | head -1)"
fi

echo ""
echo "✅  vidget installed! Try:"
echo "   vidget --help"
echo "   vidget --version"
echo "   vidget formats https://www.foxnews.com/video/6390070137112"
```

Make it executable: `chmod +x install.sh`.

---

### 8. Final integration tests — `tests/test_integration.py`

These tests run the full stack against mocked yt-dlp (no real network).

```python
import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path
from jre_vidget.cli import app
from jre_vidget.models import DownloadResult, DownloadStatus, VideoInfo

runner = CliRunner()

def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "vidget" in result.output

def test_keyboard_interrupt_handled(tmp_path):
    with patch("jre_vidget.cli.engine.download", side_effect=KeyboardInterrupt):
        result = runner.invoke(app, ["download", "https://x.com",
                                     "--output", str(tmp_path)])
    assert result.exit_code == 130

def test_config_reset(tmp_path, monkeypatch):
    monkeypatch.setattr("jre_vidget.models.CONFIG_PATH", tmp_path / "config.json")
    result = runner.invoke(app, ["config", "reset", "--yes"])
    assert result.exit_code == 0
    assert not (tmp_path / "config.json").exists()

def test_output_dir_created(tmp_path):
    new_dir = tmp_path / "new_subdir"
    fake_result = DownloadResult(
        url="https://x.com", status=DownloadStatus.SUCCESS,
        filepath=new_dir / "video.mp4"
    )
    with patch("jre_vidget.cli.engine.download", return_value=fake_result):
        result = runner.invoke(app, ["download", "https://x.com",
                                     "--output", str(new_dir)])
    assert new_dir.exists()

def test_batch_with_comments(tmp_path):
    urls_file = tmp_path / "urls.txt"
    urls_file.write_text("# comment\nhttps://x.com\n\nhttps://y.com\n")
    fake_result = DownloadResult(url="", status=DownloadStatus.SUCCESS)
    with patch("jre_vidget.cli.engine.download_batch") as mock_batch:
        mock_batch.return_value = MagicMock(
            results=[fake_result, fake_result], total=2, completed=2, failed=0
        )
        result = runner.invoke(app, ["batch", str(urls_file),
                                     "--output", str(tmp_path)])
    assert result.exit_code == 0
    called_job = mock_batch.call_args[0][0]
    assert called_job.urls == ["https://x.com", "https://y.com"]
```

---

## Acceptance criteria
- `vidget --version` prints `vidget 0.1.0`
- `vidget download <url>` retries on network failure (visible in output)
- Ctrl-C exits with code 130 and a clean error message (no traceback)
- `vidget config reset --yes` deletes the config file
- `install.sh` runs to completion on a clean machine with Python 3.11+
- `pytest` — all tests pass (aim for ≥ 20 tests across all test files)
- `ruff check src/` — zero warnings
- `mypy src/ --strict` — zero errors
