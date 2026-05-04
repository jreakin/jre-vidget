# ADR-004: ffmpeg-python as ffmpeg Wrapper

**Date:** 2026-05-03
**Status:** Accepted

## Context

HLS streams from Brightcove (Fox News CDN) are delivered as separate video-only and
audio-only streams that must be merged into a single output file. We needed a way to
invoke ffmpeg for this merging step, as well as for format conversion (e.g., mp4 → mp3).

## Decision

Use `ffmpeg-python` as the Python binding, but allow yt-dlp to handle the ffmpeg
invocation via its built-in postprocessors (`FFmpegMergerPP`, `FFmpegExtractAudio`,
`FFmpegVideoConvertor`).

## Rationale

- **yt-dlp handles the common case** — when `merge_output_format` is set in yt-dlp options,
  yt-dlp calls ffmpeg automatically for stream merging; no manual ffmpeg code needed
- **`ffmpeg-python` for future use** — listed as a dependency for any cases where we need
  direct pipeline control (thumbnail extraction, custom filters, etc.)
- **`shutil.which("ffmpeg")`** — the pre-flight check in `checks.py` verifies ffmpeg is on
  PATH without importing ffmpeg-python, keeping the warning non-fatal
- Alternatives considered: `subprocess` + raw ffmpeg args (fragile, no typing),
  `imageio-ffmpeg` (focused on image/video I/O, not general conversion)

## Consequences

- ffmpeg must be installed separately (`brew install ffmpeg`) — not a Python package
- `checks.py` warns but does not exit if ffmpeg is missing; format conversion silently
  fails in that case; users see an incomplete download
- Any future direct ffmpeg pipeline work should use `ffmpeg-python`'s fluent API,
  not subprocess calls

## Model Version

claude-sonnet-4-6
