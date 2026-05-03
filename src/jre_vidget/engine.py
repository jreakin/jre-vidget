"""
yt-dlp download engine — fetch_info, download, download_batch.

Pure business logic: no Typer/Rich. Progress is reported via optional hooks.
See prompts/phase-3-download-engine/current.md for the spec.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError

from jre_vidget.models import (
    BatchJob,
    DownloadConfig,
    DownloadResult,
    DownloadStatus,
    OutputFormat,
    Quality,
    VideoFormat,
    VideoInfo,
)

log = logging.getLogger(__name__)


class ProgressData(TypedDict, total=False):
    """Subset of yt-dlp progress dict passed to ProgressHook."""

    status: str
    downloaded_bytes: int
    total_bytes: int
    total_bytes_estimate: int
    speed: float | None
    eta: int | None
    filename: str


ProgressHook = Callable[[ProgressData], None]


class EngineError(Exception):
    """Raised when yt-dlp or ffmpeg encounters an unrecoverable error."""


def _ydl_format_for_config(config: DownloadConfig) -> str:
    if config.format.is_audio_only:
        return Quality.AUDIO.ydl_format
    return config.quality.ydl_format


def _merge_output_format(config: DownloadConfig) -> str | None:
    if config.format.is_audio_only:
        return None
    if config.format in (OutputFormat.MP4, OutputFormat.MKV, OutputFormat.MOV):
        return config.format.value
    return "mp4"


def _extract_audio_postprocessor(fmt: OutputFormat) -> dict[str, Any]:
    return {
        "key": "FFmpegExtractAudio",
        "preferredcodec": fmt.value,
    }


def _video_convert_postprocessor(fmt: OutputFormat) -> dict[str, Any]:
    return {
        "key": "FFmpegVideoConvertor",
        "preferedformat": fmt.value,
    }


def build_ydl_opts(
    config: DownloadConfig,
    progress_hook: ProgressHook | None = None,
) -> dict[str, Any]:
    """
    Translate a DownloadConfig into a yt-dlp options dict.

    Rules:
    - If config.format.is_audio_only → use FFmpegExtractAudio postprocessor
    - If config.format is a video container other than mp4 → use FFmpegVideoConvertor
    - Always merge separate video+audio streams into a single file (when not audio-only)
    - If config.subtitles is True → writesubtitles + writeautomaticsub
    - progress_hook is appended to the 'progress_hooks' list if provided
    """
    opts: dict[str, Any] = {
        "format": _ydl_format_for_config(config),
        "outtmpl": config.output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    postprocessors: list[dict[str, Any]] = []

    if config.format.is_audio_only:
        postprocessors.append(_extract_audio_postprocessor(config.format))
    else:
        merge_fmt = _merge_output_format(config)
        if merge_fmt:
            opts["merge_output_format"] = merge_fmt
        if config.format not in (OutputFormat.MP4,):
            postprocessors.append(_video_convert_postprocessor(config.format))

    if postprocessors:
        opts["postprocessors"] = postprocessors

    if config.subtitles:
        opts["writesubtitles"] = True
        opts["writeautomaticsub"] = True

    if progress_hook is not None:
        opts["progress_hooks"] = [progress_hook]

    return opts


def _format_resolution(fmt: dict[str, Any]) -> str | None:
    res = fmt.get("resolution")
    if isinstance(res, str) and res and res != "audio only":
        return res
    w, h = fmt.get("width"), fmt.get("height")
    if isinstance(w, int) and isinstance(h, int):
        return f"{w}x{h}"
    return None


def _map_video_format(fmt: dict[str, Any]) -> VideoFormat:
    filesize = fmt.get("filesize")
    if filesize is None:
        filesize = fmt.get("filesize_approx")
    fs_int: int | None = None
    if isinstance(filesize, (int, float)):
        fs_int = int(filesize)

    fps = fmt.get("fps")
    fps_f: float | None = float(fps) if isinstance(fps, (int, float)) else None

    tbr = fmt.get("tbr")
    tbr_f: float | None = float(tbr) if isinstance(tbr, (int, float)) else None

    fid = fmt.get("format_id")
    ext = fmt.get("ext")

    return VideoFormat(
        format_id=str(fid) if fid is not None else "",
        ext=str(ext) if ext is not None else "",
        resolution=_format_resolution(fmt),
        fps=fps_f,
        vcodec=fmt.get("vcodec") if isinstance(fmt.get("vcodec"), str) else None,
        acodec=fmt.get("acodec") if isinstance(fmt.get("acodec"), str) else None,
        tbr=tbr_f,
        filesize=fs_int,
    )


def _raw_to_video_info(raw: dict[str, Any], fallback_url: str) -> VideoInfo:
    webpage = raw.get("webpage_url")
    webpage_url = webpage if isinstance(webpage, str) else fallback_url
    vid = raw.get("id")
    title = raw.get("title")
    formats_raw = raw.get("formats")
    formats_list: list[VideoFormat] = []
    if isinstance(formats_raw, list):
        for item in formats_raw:
            if isinstance(item, dict):
                formats_list.append(_map_video_format(item))

    subs = raw.get("subtitles")
    subtitles: dict[str, list[dict[str, Any]]] = {}
    if isinstance(subs, dict):
        for k, v in subs.items():
            if isinstance(k, str) and isinstance(v, list):
                subtitles[k] = [x for x in v if isinstance(x, dict)]

    duration = raw.get("duration")
    dur_int: int | None = int(duration) if isinstance(duration, (int, float)) else None

    thumb = raw.get("thumbnail")
    upl = raw.get("uploader")
    udate = raw.get("upload_date")

    return VideoInfo(
        id=str(vid) if vid is not None else "",
        title=str(title) if title is not None else "",
        url=webpage_url,
        webpage_url=webpage_url,
        duration=dur_int,
        thumbnail=thumb if isinstance(thumb, str) else None,
        uploader=upl if isinstance(upl, str) else None,
        upload_date=udate if isinstance(udate, str) else None,
        formats=formats_list,
        subtitles=subtitles,
    )


def fetch_info(url: str) -> VideoInfo:
    """
    Probe a URL with yt-dlp (no download) and return a VideoInfo.

    Steps:
    1. Call yt-dlp with extract_flat=False, quiet=True, no_warnings=True
    2. Map the raw info dict → VideoInfo (and its nested VideoFormat list)
    3. Raise EngineError if yt-dlp raises DownloadError or ExtractorError
    """
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            raw = ydl.extract_info(url, download=False)
    except (DownloadError, ExtractorError) as e:
        raise EngineError(str(e)) from e

    if not isinstance(raw, dict):
        raise EngineError("extract_info returned unexpected payload")

    return _raw_to_video_info(raw, url)


def _expected_extension(config: DownloadConfig) -> str:
    return config.format.value


def _find_newest_output_file(output_dir: Path, ext: str) -> Path | None:
    ext = ext.lower().lstrip(".")
    cutoff = time.time() - 60.0
    best: tuple[float, Path] | None = None
    try:
        for path in output_dir.iterdir():
            if not path.is_file():
                continue
            if path.suffix.lower() != f".{ext}":
                continue
            mtime = path.stat().st_mtime
            if mtime < cutoff:
                continue
            if best is None or mtime > best[0]:
                best = (mtime, path)
    except OSError as e:
        log.warning("Failed to scan output_dir %s: %s", output_dir, e)
        return None
    return best[1] if best else None


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
    """
    started = time.perf_counter()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    opts = build_ydl_opts(config, progress_hook=progress_hook)

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([config.url])
    except DownloadError as e:
        elapsed = time.perf_counter() - started
        return DownloadResult(
            url=config.url,
            status=DownloadStatus.FAILED,
            filepath=None,
            error=str(e),
            duration_s=elapsed,
            finished_at=datetime.now(),
        )
    except Exception as e:
        raise EngineError(str(e)) from e

    elapsed = time.perf_counter() - started
    filepath = _find_newest_output_file(config.output_dir, _expected_extension(config))
    return DownloadResult(
        url=config.url,
        status=DownloadStatus.SUCCESS,
        filepath=filepath,
        error=None,
        duration_s=elapsed,
        finished_at=datetime.now(),
    )


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
    for url in job.urls:
        per_config = job.config.model_copy(update={"url": url})
        try:
            result = download(per_config, progress_hook)
        except EngineError as e:
            result = DownloadResult(
                url=url,
                status=DownloadStatus.FAILED,
                filepath=None,
                error=str(e),
                duration_s=None,
                finished_at=datetime.now(),
            )
        job.results.append(result)
        if on_result is not None:
            on_result(result)
    return job
