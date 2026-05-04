# ADR-001: yt-dlp for Video URL Extraction

**Date:** 2026-05-03
**Status:** Accepted

## Context

We needed a library to extract video stream URLs from sites like Fox News (Brightcove CDN),
YouTube, Twitter/X, and 1000+ others. The candidate was the original `youtube-dl` project.

## Decision

Use `yt-dlp` instead of `youtube-dl`.

## Rationale

- **Actively maintained** — yt-dlp is the community fork with weekly releases; youtube-dl had
  an 18-month gap in 2021–2022 and is now largely stale
- **Brightcove / HLS support** — Fox News videos use Brightcove CDN over HLS; yt-dlp handles
  this natively; youtube-dl requires manual patches
- **Python API** — `YoutubeDL` context manager is stable and typed enough for wrapping
- **Format selection** — yt-dlp's format filter syntax (`bestvideo[height<=720]+bestaudio`)
  maps cleanly to our `Quality` enum
- Alternatives considered: `streamlink` (streaming-focused, not download-first), raw `ffmpeg`
  + `m3u8` parsing (too low-level, fragile)

## Consequences

- Dependency on an external, community-maintained project; no SLA
- yt-dlp's internal API (`extract_info`, progress hooks) is stable but undocumented;
  we wrap it in `engine.py` to isolate breakage
- Must keep `yt-dlp` pinned with `>=` floor to get security/site patches

## Model Version

claude-sonnet-4-6
