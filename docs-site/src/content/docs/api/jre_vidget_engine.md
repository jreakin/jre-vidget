---
title: jre_vidget.engine
description: "yt-dlp download engine — fetch_info, download, download_batch."
---


yt-dlp download engine — fetch_info, download, download_batch.

Pure business logic: no Typer/Rich. Progress is reported via optional hooks.
See prompts/phase-3-download-engine/current.md for the spec.


## ProgressData Objects

```python
class ProgressData(TypedDict)
```

Subset of yt-dlp progress dict passed to ProgressHook.


## EngineError Objects

```python
class EngineError(Exception)
```

Raised when yt-dlp or ffmpeg encounters an unrecoverable error.


#### build\_ydl\_opts

```python
def build_ydl_opts(
        config: DownloadConfig,
        progress_hook: ProgressHook | None = None) -> dict[str, Any]
```

Translate a DownloadConfig into a yt-dlp options dict.

Rules:
- If config.format.is_audio_only → use FFmpegExtractAudio postprocessor
- If config.format is a video container other than mp4 → use FFmpegVideoConvertor
- Always merge separate video+audio streams into a single file (when not audio-only)
- If config.subtitles is True → writesubtitles + writeautomaticsub
- progress_hook is appended to the 'progress_hooks' list if provided


#### fetch\_info

```python
def fetch_info(url: str) -> VideoInfo
```

Probe a URL with yt-dlp (no download) and return a VideoInfo.

Steps:
1. Call yt-dlp with extract_flat=False, quiet=True, no_warnings=True
2. Map the raw info dict → VideoInfo (and its nested VideoFormat list)
3. Raise EngineError if yt-dlp raises DownloadError / ExtractorError


#### preview

```python
def preview(url: str) -> VideoPreview
```

Fetch video metadata without downloading any media.

Raises DownloadError on network failure, unsupported URL, or empty response.


#### download

```python
def download(config: DownloadConfig,
             progress_hook: ProgressHook | None = None,
             retries: int | None = None) -> DownloadResult
```

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
   `_find_newest_output_file` under ``output_dir``. Paths must lie under the
   output directory and match the expected format extension (intermediate or wrong
   suffix paths from yt-dlp are ignored so the final file can still be found via
   mtime fallback). If nothing matches, status is still ``SUCCESS`` but
   ``filepath`` is ``None`` and a warning is logged.
6. On exhausted DownloadError → return DownloadResult(status=FAILED, error=...)
7. On any other exception → re-raise as EngineError


#### download\_batch

```python
def download_batch(
        job: BatchJob,
        progress_hook: ProgressHook | None = None,
        on_result: Callable[[DownloadResult], None] | None = None) -> BatchJob
```

Download every URL in job.urls using job.config.

For each URL:
1. Create a per-URL DownloadConfig (same settings, different url)
2. Call download(per_config, progress_hook)
3. Append result to job.results
4. Call on_result(result) if provided (lets the UI update live)

Returns the mutated BatchJob with all results populated.
Never raises — failed URLs are captured in DownloadResult(status=FAILED).

