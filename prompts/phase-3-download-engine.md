# Phase 3 — Download Engine

## Goal
Implement `src/jre_vidget/engine.py` — the core yt-dlp wrapper that handles
fetching video metadata, downloading streams, and post-processing via ffmpeg.
The engine is pure Python with no UI or CLI concerns; it emits progress via a
callback so the UI layer (Phase 5) can render whatever it likes.

---

## Prerequisites
Phase 2 complete — all Pydantic models available and tests passing.

---

## Deliverables

### `src/jre_vidget/engine.py`

---

#### `ProgressHook` — typed callback signature
```python
from typing import Callable, TypedDict

class ProgressData(TypedDict, total=False):
    status:            str          # "downloading" | "finished" | "error"
    downloaded_bytes:  int
    total_bytes:       int
    total_bytes_estimate: int
    speed:             float | None  # bytes/sec
    eta:               int | None    # seconds
    filename:          str

ProgressHook = Callable[[ProgressData], None]
```

---

#### `EngineError` — domain exception
```python
class EngineError(Exception):
    """Raised when yt-dlp or ffmpeg encounters an unrecoverable error."""
```

---

#### `build_ydl_opts` — pure function, no side effects
```python
def build_ydl_opts(
    config: DownloadConfig,
    progress_hook: ProgressHook | None = None,
) -> dict:
    """
    Translate a DownloadConfig into a yt-dlp options dict.

    Rules:
    - If config.format.is_audio_only → use FFmpegExtractAudio postprocessor
    - If config.format is a video container other than mp4 → use FFmpegVideoConvertor
    - Always merge separate video+audio streams into a single file
    - If config.subtitles is True → write_subs=True, writeautomaticsub=True
    - progress_hook is appended to the 'progress_hooks' list if provided
    """
```

Implement this function in full. The output dict must be suitable to pass
directly to `yt_dlp.YoutubeDL(opts)`.

---

#### `fetch_info` — get metadata without downloading
```python
def fetch_info(url: str) -> VideoInfo:
    """
    Probe a URL with yt-dlp (no download) and return a VideoInfo.

    Steps:
    1. Call yt-dlp with extract_flat=False, quiet=True, no_warnings=True
    2. Map the raw info dict → VideoInfo (and its nested VideoFormat list)
    3. Raise EngineError if yt-dlp raises DownloadError or ExtractorError
    """
```

Key mappings from the raw yt-dlp dict:
| yt-dlp key | VideoInfo field |
|------------|----------------|
| `id` | `id` |
| `title` | `title` |
| `webpage_url` | `webpage_url` |
| `duration` | `duration` |
| `thumbnail` | `thumbnail` |
| `uploader` | `uploader` |
| `upload_date` | `upload_date` |
| `formats` | `formats` (list → `VideoFormat`) |
| `subtitles` | `subtitles` |

For each format entry, map:
| yt-dlp key | VideoFormat field |
|------------|-----------------|
| `format_id` | `format_id` |
| `ext` | `ext` |
| `resolution` | `resolution` |
| `fps` | `fps` |
| `vcodec` | `vcodec` |
| `acodec` | `acodec` |
| `tbr` | `tbr` |
| `filesize` or `filesize_approx` | `filesize` |

---

#### `download` — download a single URL
```python
def download(
    config: DownloadConfig,
    progress_hook: ProgressHook | None = None,
) -> DownloadResult:
    """
    Download a video according to config.

    Steps:
    1. Record start time
    2. Ensure config.output_dir exists (mkdir parents, exist_ok)
    3. Build opts via build_ydl_opts(config, progress_hook)
    4. Call ydl.download([config.url])
    5. On success → find the output file and return DownloadResult(status=SUCCESS)
    6. On yt_dlp.utils.DownloadError → return DownloadResult(status=FAILED, error=str(e))
    7. On any other exception → re-raise as EngineError

    Finding the output file:
    - After download, scan config.output_dir for the newest file modified
      within the last 60 seconds that matches the expected extension.
    - If nothing found, set filepath=None (download may have been a no-op
      e.g. already exists).
    """
```

---

#### `download_batch` — download multiple URLs sequentially
```python
def download_batch(
    job: BatchJob,
    progress_hook: ProgressHook | None = None,
    on_result: Callable[[DownloadResult], None] | None = None,
) -> BatchJob:
    """
    Download every URL in job.urls using job.config.

    For each URL:
    1. Create a per-URL DownloadConfig (same settings, different url)
    2. Call download(per_config, progress_hook)
    3. Append result to job.results
    4. Call on_result(result) if provided (lets the UI update live)

    Returns the mutated BatchJob with all results populated.
    Never raises — failed URLs are captured in DownloadResult(status=FAILED).
    """
```

---

## Tests to write in `tests/test_engine.py`

Use `unittest.mock` to avoid real network calls.

```python
from unittest.mock import patch, MagicMock
from jre_vidget.engine import build_ydl_opts, fetch_info, download, EngineError
from jre_vidget.models import (
    DownloadConfig, Quality, OutputFormat, DownloadStatus, BatchJob
)
from pathlib import Path

def test_build_ydl_opts_mp4():
    cfg = DownloadConfig(url="https://x.com", quality=Quality.P720, format=OutputFormat.MP4)
    opts = build_ydl_opts(cfg)
    assert "720" in opts["format"]
    assert opts["merge_output_format"] == "mp4"

def test_build_ydl_opts_mp3_uses_extract_audio():
    cfg = DownloadConfig(url="https://x.com", format=OutputFormat.MP3)
    opts = build_ydl_opts(cfg)
    pp = opts["postprocessors"]
    assert any(p["key"] == "FFmpegExtractAudio" for p in pp)

def test_build_ydl_opts_progress_hook_attached():
    hook = lambda d: None
    cfg = DownloadConfig(url="https://x.com")
    opts = build_ydl_opts(cfg, progress_hook=hook)
    assert hook in opts["progress_hooks"]

def test_fetch_info_maps_fields():
    fake_info = {
        "id": "abc123", "title": "Test Video", "webpage_url": "https://x.com",
        "duration": 305, "thumbnail": None, "uploader": None, "upload_date": None,
        "formats": [], "subtitles": {},
    }
    with patch("yt_dlp.YoutubeDL") as MockYDL:
        instance = MagicMock()
        instance.extract_info.return_value = fake_info
        MockYDL.return_value.__enter__.return_value = instance
        info = fetch_info("https://x.com")
    assert info.id == "abc123"
    assert info.duration_str == "5:05"

def test_download_returns_failed_on_error():
    cfg = DownloadConfig(url="https://x.com")
    with patch("yt_dlp.YoutubeDL") as MockYDL:
        import yt_dlp
        instance = MagicMock()
        instance.download.side_effect = yt_dlp.utils.DownloadError("404")
        MockYDL.return_value.__enter__.return_value = instance
        result = download(cfg)
    assert result.status == DownloadStatus.FAILED
    assert "404" in result.error
```

---

## Acceptance criteria
- `pytest tests/test_engine.py` passes (5 tests, green)
- `fetch_info("https://www.foxnews.com/video/6390070137112")` returns a valid
  `VideoInfo` with title, duration, and at least one format (manual smoke test)
- `mypy src/jre_vidget/engine.py --strict` passes
- No imports of `typer`, `rich`, or any UI module in `engine.py`
