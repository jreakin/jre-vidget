"""
yt-dlp download engine — fetch_info, download, download_batch.

Pure business logic: no Typer/Rich. Progress is reported via optional hooks.
See prompts/phase-3-download-engine/current.md for the spec.
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict, cast

import yt_dlp
from yt_dlp.utils import DownloadError as YtdlpDownloadError
from yt_dlp.utils import ExtractorError

from jre_vidget.models import (
    BatchJob,
    DownloadConfig,
    DownloadError,
    DownloadResult,
    DownloadStatus,
    OutputFormat,
    Quality,
    VideoFormat,
    VideoInfo,
    VideoPreview,
)

log = logging.getLogger(__name__)

# Bound network waits for yt-dlp extract/download (seconds).
YDL_SOCKET_TIMEOUT_SECONDS = 30


def _base_ydl_opts() -> dict[str, Any]:
    """Shared yt-dlp flags for all engine call sites (quiet, single video, no playlist)."""
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": YDL_SOCKET_TIMEOUT_SECONDS,
    }


# yt-dlp retry back-off between attempts (seconds).
RETRY_BACKOFF_SECONDS = 2.0
# Only consider output files modified within this window when the finished hook
# did not report a path (seconds).
FILE_DISCOVERY_WINDOW_SECONDS = 60.0


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


class _ExtractionError(Exception):
    """Internal: ``extract_info`` failed or returned a non-dict payload."""

    __slots__ = ()


def _extract_raw_info(
    url: str,
    extra_opts: dict[str, Any],
    *,
    non_dict_message: str = "extract_info returned unexpected payload",
) -> dict[str, Any]:
    """
    Run yt-dlp ``extract_info(..., download=False)`` with shared base opts.

    Callers map :class:`_ExtractionError` to :class:`EngineError` or :class:`DownloadError`.
    """
    opts: dict[str, Any] = {**_base_ydl_opts(), **extra_opts}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            raw = ydl.extract_info(url, download=False)
    except (YtdlpDownloadError, ExtractorError) as e:
        raise _ExtractionError(str(e)) from e
    if not isinstance(raw, dict):
        raise _ExtractionError(non_dict_message)
    return raw


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
        **_base_ydl_opts(),
        "format": _ydl_format_for_config(config),
        "outtmpl": config.output_template,
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
    3. Raise EngineError if yt-dlp raises DownloadError / ExtractorError
    """
    try:
        raw = _extract_raw_info(url, {"extract_flat": False})
    except _ExtractionError as e:
        raise EngineError(str(e)) from e

    return _raw_to_video_info(raw, url)


def _thumbnail_url_from_info(info: dict[str, Any]) -> str:
    thumb = info.get("thumbnail")
    if isinstance(thumb, str):
        return thumb
    thumbs = info.get("thumbnails")
    if isinstance(thumbs, list):
        for entry in reversed(thumbs):
            if not isinstance(entry, dict):
                continue
            row = cast(dict[str, Any], entry)
            u = row.get("url")
            if isinstance(u, str) and u:
                return u
    return ""


def _preview_format_labels(info: dict[str, Any]) -> list[str]:
    formats_raw = info.get("formats")
    labels: list[str] = []
    if not isinstance(formats_raw, list):
        return labels
    for item in formats_raw:
        if not isinstance(item, dict):
            continue
        fn = item.get("format_note")
        label: str | None = None
        if isinstance(fn, str) and fn and fn.lower() != "none":
            label = fn
        else:
            label = _format_resolution(item)
        if label and label not in labels:
            labels.append(label)
    return labels


def preview(url: str) -> VideoPreview:
    """
    Fetch video metadata without downloading any media.

    Raises DownloadError on network failure, unsupported URL, or empty response.
    """
    try:
        raw_info = _extract_raw_info(
            url,
            {"skip_download": True, "extract_flat": False},
            non_dict_message=f"No metadata returned for {url}",
        )
    except _ExtractionError as e:
        raise DownloadError(str(e)) from e

    desc = raw_info.get("description")
    description = desc if isinstance(desc, str) else ""
    duration = raw_info.get("duration")
    duration_seconds = int(duration) if isinstance(duration, (int, float)) else 0
    title_raw = raw_info.get("title")
    title = title_raw if isinstance(title_raw, str) else ""
    upl = raw_info.get("uploader")
    uploader = upl if isinstance(upl, str) else ""

    vc = raw_info.get("view_count")
    view_count: int | None = int(vc) if isinstance(vc, (int, float)) else None

    ch = raw_info.get("channel_url")
    channel_url = ch if isinstance(ch, str) else None

    udate = raw_info.get("upload_date")
    upload_date = udate if isinstance(udate, str) else None

    return VideoPreview(
        url=url,
        title=title,
        description=description,
        duration_seconds=duration_seconds,
        thumbnail_url=_thumbnail_url_from_info(raw_info),
        uploader=uploader,
        channel_url=channel_url,
        view_count=view_count,
        upload_date=upload_date,
        formats=_preview_format_labels(raw_info),
    )


def _expected_extension(config: DownloadConfig) -> str:
    return config.format.value


def _find_newest_output_file(output_dir: Path, ext: str) -> Path | None:
    ext = ext.lower().lstrip(".")
    cutoff = time.time() - FILE_DISCOVERY_WINDOW_SECONDS
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


def _emit_retry_log(url: str, attempt_1_based: int, max_retries: int) -> None:
    """Human-visible retry line on stderr (no Rich / Typer in engine)."""
    sys.stderr.write(f"⟳  Retry {attempt_1_based}/{max_retries} for {url}\n")
    sys.stderr.flush()


def download(
    config: DownloadConfig,
    progress_hook: ProgressHook | None = None,
    retries: int | None = None,
) -> DownloadResult:
    """
    Download a video according to config.

    Steps:
    1. Record start time
    2. Ensure config.output_dir exists (mkdir parents, exist_ok)
    3. Build opts via build_ydl_opts(config, progress_hook)
    4. Call ydl.download([config.url]), retrying on DownloadError up to ``retries``
       times (from ``config.retries`` when ``retries`` is None) with
       ``RETRY_BACKOFF_SECONDS`` between attempts
    5. On success → find the output file and return DownloadResult(status=SUCCESS)
    6. On exhausted DownloadError → return DownloadResult(status=FAILED, error=...)
    7. On any other exception → re-raise as EngineError
    """
    started = time.perf_counter()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    finished_paths: list[Path] = []

    def _wrapped_progress_hook(d: ProgressData) -> None:
        if progress_hook is not None:
            progress_hook(d)
        if d.get("status") == "finished":
            fn = d.get("filename")
            if isinstance(fn, str) and fn.strip():
                finished_paths.append(Path(fn))

    opts = build_ydl_opts(config, progress_hook=_wrapped_progress_hook)
    max_retries = config.retries if retries is None else retries

    attempt = 0
    while True:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([config.url])
        except YtdlpDownloadError as e:
            if attempt < max_retries:
                _emit_retry_log(config.url, attempt + 1, max_retries)
                time.sleep(RETRY_BACKOFF_SECONDS)
                attempt += 1
                finished_paths.clear()
                continue
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
        filepath: Path | None = None
        for candidate in reversed(finished_paths):
            if candidate.is_file():
                filepath = candidate
                break
        if filepath is None:
            filepath = _find_newest_output_file(
                config.output_dir,
                _expected_extension(config),
            )
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
    hook_lock = threading.Lock()

    def _safe_progress_hook(d: ProgressData) -> None:
        if progress_hook is None:
            return
        with hook_lock:
            progress_hook(d)

    def _run_one(url: str) -> DownloadResult:
        per_config = job.config.model_copy(update={"url": url})
        try:
            result = download(per_config, _safe_progress_hook)
        except EngineError as e:
            result = DownloadResult(
                url=url,
                status=DownloadStatus.FAILED,
                filepath=None,
                error=str(e),
                duration_s=None,
                finished_at=datetime.now(),
            )
        if on_result is not None:
            with hook_lock:
                on_result(result)
        return result

    n = len(job.urls)
    if n == 0:
        return job

    max_workers = max(1, min(n, job.config.max_concurrent))
    if max_workers == 1:
        for url in job.urls:
            job.results.append(_run_one(url))
        return job

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_one, url) for url in job.urls]
        for fut in futures:
            job.results.append(fut.result())
    return job
