---
title: Download & formats
description: Quality presets, output formats, output paths, and retries for vidget download.
sidebar:
  order: 20
---

Downloads go through **yt-dlp** with options built from **`DownloadConfig`** (`jre_vidget.models`) and **`build_ydl_opts`** / **`download`** in **`jre_vidget.engine`**.

## Quality and format

- **Quality** (`best`, `1080p`, `720p`, `480p`, `audio`) maps to yt-dlp **format** selectors that merge best video+audio when not audio-only.
- **Output format** (`mp4`, `mkv`, `mov`, or audio codecs such as `mp3`, `m4a`) determines muxing and ffmpeg **postprocessors** (extract audio vs merge vs convert).

Audio-only targets skip video merge and use **`FFmpegExtractAudio`** with the chosen codec.

## Where files land

Default output directory comes from user config (`AppConfig.output_dir`, usually under your home directory). Each job uses an **`outtmpl`** pattern so filenames include title and id — see **`DownloadConfig.output_template`**.

## Retries and batch

- **`retries`** on a download job controls yt-dlp **`DownloadError`** retry loops with backoff (`engine.RETRY_BACKOFF_SECONDS`).
- **`batch`** runs many URLs with shared settings; concurrency is capped by **`max_concurrent`** on the shared **`DownloadConfig`**.

## Subtitles

When enabled, the engine sets yt-dlp **`writesubtitles`** and **`writeautomaticsub`** so subtitles are fetched alongside media when available.

## Next steps

- CLI flags: `vidget download --help`
- Types and enums: **API Reference → `jre_vidget.models`**
- Implementation detail: **`jre_vidget.engine`**
