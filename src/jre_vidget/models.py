"""
Pydantic v2 data models for jre-vidget.

Shared between the CLI, engine, and UI. Validation and serialization only.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, SecretStr

BYTES_PER_MB = 1_048_576


def _format_duration(seconds: int) -> str:
    """Format whole seconds as ``H:MM:SS`` when hours > 0, else ``M:SS``."""
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class YtdlpStatus(StrEnum):
    """yt-dlp ``progress_hooks`` payload ``status`` values handled in engine / UI."""

    DOWNLOADING = "downloading"
    FINISHED = "finished"
    ERROR = "error"


class Quality(StrEnum):
    """Supported download quality presets."""

    BEST = "best"
    P1080 = "1080p"
    P720 = "720p"
    P480 = "480p"
    AUDIO = "audio"

    @property
    def ydl_format(self) -> str:
        return {
            Quality.BEST: "bestvideo+bestaudio/best",
            Quality.P1080: "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            Quality.P720: "bestvideo[height<=720]+bestaudio/best[height<=720]",
            Quality.P480: "bestvideo[height<=480]+bestaudio/best[height<=480]",
            Quality.AUDIO: "bestaudio/best",
        }[self]


class OutputFormat(StrEnum):
    """Supported output container / codec targets."""

    MP4 = "mp4"
    MKV = "mkv"
    MOV = "mov"
    MP3 = "mp3"
    M4A = "m4a"
    AAC = "aac"
    WAV = "wav"
    FLAC = "flac"

    @property
    def is_audio_only(self) -> bool:
        return self in {
            OutputFormat.MP3,
            OutputFormat.M4A,
            OutputFormat.AAC,
            OutputFormat.WAV,
            OutputFormat.FLAC,
        }


class VideoFormat(BaseModel):
    """One available stream format from yt-dlp."""

    model_config = ConfigDict(extra="forbid")

    format_id: str
    ext: str
    resolution: str | None = None
    fps: float | None = None
    vcodec: str | None = None
    acodec: str | None = None
    tbr: float | None = None
    filesize: int | None = None

    @property
    def is_audio_only(self) -> bool:
        return self.vcodec in (None, "none")

    @property
    def display_size(self) -> str:
        if self.filesize is None:
            return "unknown"
        mb = self.filesize / BYTES_PER_MB
        return f"{mb:.1f} MB"


class DownloadError(Exception):
    """Metadata extraction failed (preview / probe) — wraps yt-dlp extract errors."""


class VideoPreview(BaseModel):
    """Metadata fetched before download — used to confirm before upload."""

    model_config = ConfigDict(extra="forbid")

    url: str
    title: str
    description: str
    duration_seconds: int
    thumbnail_url: str
    uploader: str
    channel_url: str | None = None
    view_count: int | None = None
    upload_date: str | None = None  # YYYYMMDD string from yt-dlp
    formats: list[str] = Field(default_factory=list)  # e.g. ["1080p60", "720p", "480p"]

    @property
    def duration_display(self) -> str:
        """Return HH:MM:SS or MM:SS string."""
        return _format_duration(self.duration_seconds)


class VideoInfo(BaseModel):
    """Metadata for a single URL from yt-dlp."""

    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    url: str
    webpage_url: str
    duration: int | None = None
    thumbnail: str | None = None
    uploader: str | None = None
    upload_date: str | None = None
    formats: list[VideoFormat] = Field(default_factory=list)
    subtitles: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)

    @property
    def duration_str(self) -> str:
        if self.duration is None:
            return "unknown"
        return _format_duration(self.duration)

    @property
    def best_formats(self) -> list[VideoFormat]:
        """Distinct-resolution video formats, sorted best-first by bitrate."""
        seen: set[str] = set()
        result: list[VideoFormat] = []
        for f in sorted(self.formats, key=lambda x: x.tbr or 0, reverse=True):
            key = f.resolution or f.format_id
            if key not in seen and not f.is_audio_only:
                seen.add(key)
                result.append(f)
        return result


class DownloadConfig(BaseModel):
    """Options for a single download job."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    url: str
    quality: Quality = Quality.BEST
    format: OutputFormat = OutputFormat.MP4
    output_dir: Path = Field(default_factory=lambda: Path.home() / "Downloads")
    subtitles: bool = False
    retries: int = Field(default=2, ge=0, le=5)
    max_concurrent: int = Field(default=3, ge=1, le=32)

    @property
    def output_template(self) -> str:
        return str(self.output_dir / "%(title)s [%(id)s].%(ext)s")


# ---------------------------------------------------------------------------
# YouTube publish models
# ---------------------------------------------------------------------------


class AuthConfig(BaseModel):
    """YouTube OAuth credentials — persisted inside AppConfig."""

    model_config = ConfigDict(extra="forbid")

    client_id: str | None = None
    client_secret: SecretStr | None = None
    refresh_token: SecretStr | None = None


class PrivacyStatus(StrEnum):
    """YouTube video privacy — matches Data API ``status.privacyStatus`` values."""

    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class PublishConfig(BaseModel):
    """Options for a single YouTube upload job."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    filepath: Path
    title: str  # required — no default
    description: str = ""
    privacy: PrivacyStatus = PrivacyStatus.PUBLIC
    remove_after_upload: bool = False


class PublishResult(BaseModel):
    """Outcome of a completed YouTube upload."""

    model_config = ConfigDict(extra="forbid")

    video_id: str
    url: str  # https://youtube.com/watch?v=...
    title: str
    privacy: PrivacyStatus
    removed_local_file: bool = False


class AppConfig(BaseModel):
    """User preferences persisted under ~/.vidget/config.json."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    output_dir: Path = Field(default_factory=lambda: Path.home() / "Downloads")
    quality: Quality = Quality.BEST
    format: OutputFormat = OutputFormat.MP4
    subtitles: bool = False
    max_concurrent: int = 3
    auth: AuthConfig = Field(default_factory=AuthConfig)

    @classmethod
    def load(cls) -> AppConfig:
        from jre_vidget import config as _app_config

        return _app_config.load_app_config()

    def save(self) -> None:
        """Write config to disk with plaintext OAuth secrets (not ``model_dump_json`` masking)."""
        from jre_vidget import config as _app_config

        _app_config.save_app_config(self)


class DownloadStatus(StrEnum):
    """Terminal status of a download attempt."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class DownloadResult(BaseModel):
    """Outcome of a completed download job."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    url: str
    status: DownloadStatus
    filepath: Path | None = None
    error: str | None = None
    duration_s: float | None = None
    finished_at: datetime = Field(default_factory=datetime.now)


class BatchJob(BaseModel):
    """Batch of URLs using one DownloadConfig."""

    model_config = ConfigDict(extra="forbid")

    urls: list[str]
    config: DownloadConfig
    results: list[DownloadResult] = Field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.urls)

    @property
    def completed(self) -> int:
        return sum(1 for r in self.results if r.status == DownloadStatus.SUCCESS)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == DownloadStatus.FAILED)
