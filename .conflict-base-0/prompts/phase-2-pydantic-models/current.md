# Phase 2 — Pydantic Models
# Version: 0.1.0
# Model: claude-sonnet-4-6
# Last Updated: 2026-05-03
# Maintainer: jreakin
# Status: Draft

---

## Goal
Implement all data models in `src/jre_vidget/models.py` using Pydantic v2.
These models are the shared language between the CLI, the engine, and the UI.
No logic beyond validation and serialisation lives here.

---

## Prerequisites
Phase 1 complete — project installs and `vidget --help` works.

---

## Deliverables

### `src/jre_vidget/models.py`

Implement the following models **in this order** (each builds on the last).

---

#### `Quality` — enum of supported download qualities
```python
from enum import Enum

class Quality(str, Enum):
    BEST   = "best"
    P1080  = "1080p"
    P720   = "720p"
    P480   = "480p"
    AUDIO  = "audio"
```
Map each value to a yt-dlp format string via a property:
```python
@property
def ydl_format(self) -> str:
    return {
        Quality.BEST:  "bestvideo+bestaudio/best",
        Quality.P1080: "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        Quality.P720:  "bestvideo[height<=720]+bestaudio/best[height<=720]",
        Quality.P480:  "bestvideo[height<=480]+bestaudio/best[height<=480]",
        Quality.AUDIO: "bestaudio/best",
    }[self]
```

---

#### `OutputFormat` — enum of supported output containers
```python
class OutputFormat(str, Enum):
    MP4  = "mp4"
    MKV  = "mkv"
    MOV  = "mov"
    MP3  = "mp3"
    M4A  = "m4a"
    AAC  = "aac"
    WAV  = "wav"
    FLAC = "flac"

    @property
    def is_audio_only(self) -> bool:
        return self in {OutputFormat.MP3, OutputFormat.M4A,
                        OutputFormat.AAC, OutputFormat.WAV, OutputFormat.FLAC}
```

---

#### `VideoFormat` — a single available stream format from yt-dlp
```python
class VideoFormat(BaseModel):
    format_id:  str
    ext:        str
    resolution: str | None = None   # e.g. "1280x720" or "audio only"
    fps:        float | None = None
    vcodec:     str | None = None
    acodec:     str | None = None
    tbr:        float | None = None  # total bitrate kbps
    filesize:   int | None = None    # bytes, may be None

    @property
    def is_audio_only(self) -> bool:
        return self.vcodec in (None, "none")

    @property
    def display_size(self) -> str:
        if self.filesize is None:
            return "unknown"
        mb = self.filesize / 1_048_576
        return f"{mb:.1f} MB"
```

---

#### `VideoInfo` — metadata returned by yt-dlp for a URL
```python
class VideoInfo(BaseModel):
    id:          str
    title:       str
    url:         str
    webpage_url: str
    duration:    int | None = None   # seconds
    thumbnail:   str | None = None
    uploader:    str | None = None
    upload_date: str | None = None   # YYYYMMDD
    formats:     list[VideoFormat] = []
    subtitles:   dict[str, list[dict]] = {}

    @property
    def duration_str(self) -> str:
        if self.duration is None:
            return "unknown"
        m, s = divmod(self.duration, 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    @property
    def best_formats(self) -> list[VideoFormat]:
        """Return only distinct-resolution video formats, sorted best-first."""
        seen: set[str] = set()
        result = []
        for f in sorted(self.formats, key=lambda x: x.tbr or 0, reverse=True):
            key = f.resolution or f.format_id
            if key not in seen and not f.is_audio_only:
                seen.add(key)
                result.append(f)
        return result
```

---

#### `DownloadConfig` — options for a single download job
```python
from pathlib import Path

class DownloadConfig(BaseModel):
    url:        str
    quality:    Quality      = Quality.BEST
    format:     OutputFormat = OutputFormat.MP4
    output_dir: Path         = Path.home() / "Downloads"
    subtitles:  bool         = False

    model_config = {"arbitrary_types_allowed": True}

    @property
    def output_template(self) -> str:
        return str(self.output_dir / "%(title)s [%(id)s].%(ext)s")
```

---

#### `AppConfig` — user's persistent preferences (saved to disk)
```python
CONFIG_PATH = Path.home() / ".vidget" / "config.json"

class AppConfig(BaseModel):
    output_dir:     Path         = Path.home() / "Downloads"
    quality:        Quality      = Quality.BEST
    format:         OutputFormat = OutputFormat.MP4
    subtitles:      bool         = False
    max_concurrent: int          = 3

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def load(cls) -> "AppConfig":
        if CONFIG_PATH.exists():
            return cls.model_validate_json(CONFIG_PATH.read_text())
        return cls()

    def save(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(self.model_dump_json(indent=2))
```

---

#### `DownloadResult` — outcome of a completed download job
```python
from datetime import datetime

class DownloadStatus(str, Enum):
    SUCCESS = "success"
    FAILED  = "failed"
    SKIPPED = "skipped"

class DownloadResult(BaseModel):
    url:        str
    status:     DownloadStatus
    filepath:   Path | None = None
    error:      str | None = None
    duration_s: float | None = None   # wall-clock seconds taken
    finished_at: datetime = Field(default_factory=datetime.now)

    model_config = {"arbitrary_types_allowed": True}
```

---

#### `BatchJob` — a collection of URLs to download together
```python
class BatchJob(BaseModel):
    urls:    list[str]
    config:  DownloadConfig
    results: list[DownloadResult] = []

    @property
    def total(self) -> int:
        return len(self.urls)

    @property
    def completed(self) -> int:
        return sum(1 for r in self.results if r.status == DownloadStatus.SUCCESS)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == DownloadStatus.FAILED)
```

---

## Tests to write in `tests/test_models.py`

```python
def test_quality_ydl_format():
    assert "720" in Quality.P720.ydl_format

def test_video_format_audio_only():
    f = VideoFormat(format_id="a1", ext="m4a", vcodec="none")
    assert f.is_audio_only

def test_app_config_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr("jre_vidget.models.CONFIG_PATH", tmp_path / "config.json")
    cfg = AppConfig(quality=Quality.P720)
    cfg.save()
    loaded = AppConfig.load()
    assert loaded.quality == Quality.P720

def test_batch_job_counts():
    cfg = DownloadConfig(url="https://example.com")
    job = BatchJob(urls=["a", "b", "c"], config=cfg)
    job.results.append(DownloadResult(url="a", status=DownloadStatus.SUCCESS))
    job.results.append(DownloadResult(url="b", status=DownloadStatus.FAILED))
    assert job.completed == 1
    assert job.failed == 1
```

---

## Acceptance criteria
- All models import without error
- `pytest tests/test_models.py` passes (4 tests, green)
- `mypy src/jre_vidget/models.py --strict` passes with no errors
- `ruff check src/` still clean
