"""
yt-dlp download engine — fetch_info, download, download_batch.

Pure business logic: no Typer/Rich. Progress is reported via optional hooks.
See prompts/phase-3-download-engine/current.md for the spec.
"""

from __future__ import annotations

import logging
import math
import sys
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
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
    YtdlpStatus,
)

log = logging.getLogger(__name__)

YDL_SOCKET_TIMEOUT_SECONDS = 30

# yt-dlp JSON / progress-hook sentinels (avoid scattering magic strings)
_YT_RESOLUTION_AUDIO_ONLY = "audio only"
_YT_FORMAT_NOTE_PLACEHOLDERS: frozenset[str] = frozenset({"none"})
_YTDL_PROGRESS_STATUSES_RECORD_OUTPUT: frozenset[str] = frozenset(
    {YtdlpStatus.FINISHED.value},
)


def _base_ydl_opts() -> dict[str, Any]:
    """Shared yt-dlp flags for all engine call sites (quiet, single video, no playlist)."""
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": YDL_SOCKET_TIMEOUT_SECONDS,
    }


RETRY_BACKOFF_SECONDS = 2.0
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
    error: str


ProgressHook = Callable[[ProgressData], None]


def _coerce_int(value: Any) -> int | None:
    """
    Return a whole number from yt-dlp JSON scalars.

    Rejects ``bool`` (``bool`` subclasses ``int``) and non-finite floats so callers
    do not treat accidental truthiness or ``NaN`` as valid metadata.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return int(value)
    return None


def _coerce_float(value: Any) -> float | None:
    """Return a finite float from yt-dlp JSON scalars; rejects ``bool``."""
    if isinstance(value, bool):
        return None
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return value
    if isinstance(value, int):
        return float(value)
    return None


def _str_field(raw: dict[str, Any], key: str, default: str = "") -> str:
    """Return ``raw[key]`` when it is a ``str``, else ``default``."""
    val = raw.get(key)
    return val if isinstance(val, str) else default


def _optional_str_field(raw: dict[str, Any], key: str) -> str | None:
    """Return ``raw[key]`` when it is a ``str``, else ``None``."""
    val = raw.get(key)
    return val if isinstance(val, str) else None


def _coerced_str_field(raw: dict[str, Any], key: str, default: str = "") -> str:
    """
    Stringify ``raw[key]`` when it is a ``str``, ``int``, or finite ``float``.

    Rejects ``bool`` (subclasses ``int``). Other types yield ``default``.
    Use for yt-dlp fields that are usually strings but may appear as numeric scalars.
    """
    val = raw.get(key)
    if isinstance(val, str):
        return val
    if isinstance(val, bool):
        return default
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        if not math.isfinite(val):
            return default
        return str(val)
    return default


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
    if isinstance(res, str) and res and res != _YT_RESOLUTION_AUDIO_ONLY:
        return res
    w, h = fmt.get("width"), fmt.get("height")
    if isinstance(w, int) and isinstance(h, int):
        return f"{w}x{h}"
    return None


def _map_video_format(fmt: dict[str, Any]) -> VideoFormat:
    filesize = fmt.get("filesize")
    if filesize is None:
        filesize = fmt.get("filesize_approx")
    fs_int = _coerce_int(filesize)

    fps = fmt.get("fps")
    fps_f = _coerce_float(fps)

    tbr = fmt.get("tbr")
    tbr_f = _coerce_float(tbr)

    return VideoFormat(
        format_id=_coerced_str_field(fmt, "format_id"),
        ext=_coerced_str_field(fmt, "ext"),
        resolution=_format_resolution(fmt),
        fps=fps_f,
        vcodec=_optional_str_field(fmt, "vcodec"),
        acodec=_optional_str_field(fmt, "acodec"),
        tbr=tbr_f,
        filesize=fs_int,
    )


def _raw_to_video_info(raw: dict[str, Any], fallback_url: str) -> VideoInfo:
    _wu = _optional_str_field(raw, "webpage_url")
    webpage_url = fallback_url if _wu is None else _wu
    title = _coerced_str_field(raw, "title")
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
    dur_int = _coerce_int(duration)

    return VideoInfo(
        id=_coerced_str_field(raw, "id"),
        title=title,
        url=webpage_url,
        webpage_url=webpage_url,
        duration=dur_int,
        thumbnail=_optional_str_field(raw, "thumbnail"),
        uploader=_optional_str_field(raw, "uploader"),
        upload_date=_optional_str_field(raw, "upload_date"),
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
    # Use _optional_str_field for type safety; keep "" short-circuit (do not prefer thumbnails).
    thumb = _optional_str_field(info, "thumbnail")
    if thumb:
        return thumb
    if thumb == "":
        return ""
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
        if isinstance(fn, str) and fn and fn.lower() not in _YT_FORMAT_NOTE_PLACEHOLDERS:
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

    description = _coerced_str_field(raw_info, "description")
    duration = raw_info.get("duration")
    duration_seconds = _coerce_int(duration) or 0
    title = _coerced_str_field(raw_info, "title")
    uploader = _coerced_str_field(raw_info, "uploader")

    vc = raw_info.get("view_count")
    view_count = _coerce_int(vc)

    channel_url = _optional_str_field(raw_info, "channel_url")
    upload_date = _optional_str_field(raw_info, "upload_date")

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


def _resolve_output_base(output_dir: Path) -> Path:
    """
    Best-effort canonical directory for containment checks and mtime fallback.

    Prefer :meth:`Path.resolve`; on ``OSError`` fall back to :meth:`Path.absolute` so
    :func:`download` and :func:`_find_newest_output_file` share the same anchor when
    ``resolve`` is unavailable (permissions, transient FS errors).
    """
    try:
        return output_dir.resolve()
    except OSError:
        try:
            return output_dir.absolute()
        except OSError:
            return output_dir


def _is_under_output_dir(candidate: Path, output_dir_resolved: Path) -> bool:
    """True when ``candidate`` resolves to a file inside ``output_dir_resolved`` (no path escape)."""
    try:
        resolved = candidate.resolve()
    except OSError:
        return False
    try:
        resolved.relative_to(output_dir_resolved)
    except ValueError:
        return False
    return resolved.is_file()


def _find_newest_output_file(output_dir: Path, ext: str) -> Path | None:
    """
    Fallback when yt-dlp hooks did not record a final path.

    Picks the newest ``.{ext}`` file under ``output_dir`` (resolved) within
    :data:`FILE_DISCOVERY_WINDOW_SECONDS`, ignoring files outside the output tree.
    """
    ext = ext.lower().lstrip(".")
    base = _resolve_output_base(output_dir)
    cutoff = time.time() - FILE_DISCOVERY_WINDOW_SECONDS
    best: tuple[float, Path] | None = None
    try:
        for path in output_dir.iterdir():
            if not path.is_file():
                continue
            if path.suffix.lower() != f".{ext}":
                continue
            if not _is_under_output_dir(path, base):
                continue
            mtime = path.stat().st_mtime
            if mtime < cutoff:
                continue
            if best is None or mtime > best[0]:
                best = (mtime, path.resolve())
    except OSError as e:
        log.warning("Failed to scan output_dir %s: %s", output_dir, e)
        return None
    return best[1] if best else None


def _emit_retry_log(url: str, attempt_1_based: int, max_retries: int) -> None:
    """Human-visible retry line on stderr (no Rich / Typer in engine)."""
    sys.stderr.write(f"⟳  Retry {attempt_1_based}/{max_retries} for {url}\n")
    sys.stderr.flush()


def _attempt_download_once(url: str, opts: dict[str, Any]) -> None:
    """
    Run a single yt-dlp download pass.

    Typically raises :class:`YtdlpDownloadError` for recoverable yt-dlp failures
    (the ``download`` retry loop handles those). Any other exception propagates to
    the caller, which maps unknown failures to :class:`EngineError`.
    """
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])


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
    3. Build opts via ``build_ydl_opts(config, progress_hook)``, then append a
       ``postprocessor_hooks`` entry so yt-dlp reports the final filepath after merge /
       ffmpeg (when postprocessors run).
    4. Call ``ydl.download([config.url])``, retrying on DownloadError up to ``retries``
       times (from ``config.retries`` when ``retries`` is None) with
       ``RETRY_BACKOFF_SECONDS`` between attempts
    5. On success → resolve the output path in order: last valid **postprocessor**
       ``finished`` filepath, then last valid **progress** ``finished`` filename, then
       :func:`_find_newest_output_file` under ``output_dir``. Paths must lie under the
       output directory and match the expected format extension (intermediate or wrong
       suffix paths from yt-dlp are ignored so the final file can still be found via
       mtime fallback). If nothing matches, status is still ``SUCCESS`` but
       ``filepath`` is ``None`` and a warning is logged.
    6. On exhausted DownloadError → return DownloadResult(status=FAILED, error=...)
    7. On any other exception → re-raise as EngineError
    """
    started = time.perf_counter()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    progress_finished_paths: list[Path] = []
    postprocessor_finished_paths: list[Path] = []

    output_base = _resolve_output_base(config.output_dir)

    ext_suffix = f".{_expected_extension(config).lower().lstrip('.')}"

    def _record_if_valid_output(path: Path, bucket: list[Path]) -> None:
        if not _is_under_output_dir(path, output_base):
            return
        # Match configured container extension only: ignore yt-dlp intermediates
        # (.part, pre-merge names) so they do not occupy hook slots; mtime fallback
        # still discovers the final file when hooks omit the true output.
        if path.suffix.lower() != ext_suffix:
            return
        bucket.append(path.resolve())

    def _wrapped_progress_hook(d: ProgressData) -> None:
        if progress_hook is not None:
            progress_hook(d)
        if d.get("status") in _YTDL_PROGRESS_STATUSES_RECORD_OUTPUT:
            fn = d.get("filename")
            if isinstance(fn, str) and fn.strip():
                _record_if_valid_output(Path(fn), progress_finished_paths)

    def _postprocessor_hook(d: dict[str, Any]) -> None:
        # yt-dlp calls this with ``status`` ``started`` / ``finished``; ``filepath`` is set when done.
        if d.get("status") != "finished":
            return
        fp = d.get("filepath")
        if isinstance(fp, str) and fp.strip():
            _record_if_valid_output(Path(fp), postprocessor_finished_paths)

    opts = build_ydl_opts(config, progress_hook=_wrapped_progress_hook)
    existing_pp_hooks = list(opts.get("postprocessor_hooks") or [])
    opts["postprocessor_hooks"] = existing_pp_hooks + [_postprocessor_hook]
    max_retries = config.retries if retries is None else retries

    attempt = 0
    while True:
        try:
            _attempt_download_once(config.url, opts)
        except YtdlpDownloadError as e:
            if attempt < max_retries:
                _emit_retry_log(config.url, attempt + 1, max_retries)
                time.sleep(RETRY_BACKOFF_SECONDS)
                attempt += 1
                progress_finished_paths.clear()
                postprocessor_finished_paths.clear()
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
        for candidate in reversed(postprocessor_finished_paths):
            if candidate.is_file():
                filepath = candidate
                break
        if filepath is None:
            for candidate in reversed(progress_finished_paths):
                if candidate.is_file():
                    filepath = candidate
                    break
        if filepath is None:
            filepath = _find_newest_output_file(
                config.output_dir,
                _expected_extension(config),
            )
        if filepath is None:
            log.warning(
                "Download finished for %s but no output filepath was resolved "
                "(output_dir=%s, ext=%s). Hooks may not have reported a final file, or "
                "nothing matched inside the discovery window.",
                config.url,
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


@dataclass
class _BatchWorker:
    """
    Encapsulates concurrent batch download: serialized progress / on_result callbacks,
    per-URL :func:`download`, and executor fan-out.
    """

    job: BatchJob
    progress_hook: ProgressHook | None = None
    on_result: Callable[[DownloadResult], None] | None = None
    _hook_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def _safe_progress_hook(self, d: ProgressData) -> None:
        if self.progress_hook is None:
            return
        with self._hook_lock:
            self.progress_hook(d)

    def _run_one(self, url: str) -> DownloadResult:
        per_config = self.job.config.model_copy(update={"url": url})
        try:
            result = download(per_config, self._safe_progress_hook)
        except EngineError as e:
            result = DownloadResult(
                url=url,
                status=DownloadStatus.FAILED,
                filepath=None,
                error=str(e),
                duration_s=None,
                finished_at=datetime.now(),
            )
        if self.on_result is not None:
            with self._hook_lock:
                self.on_result(result)
        return result

    def run(self) -> BatchJob:
        n = len(self.job.urls)
        if n == 0:
            return self.job

        max_workers = max(1, min(n, self.job.config.max_concurrent))
        if max_workers == 1:
            for url in self.job.urls:
                self.job.results.append(self._run_one(url))
            return self.job

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._run_one, url) for url in self.job.urls]
            for fut in futures:
                self.job.results.append(fut.result())
        return self.job


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
    return _BatchWorker(job, progress_hook, on_result).run()
