# jre-vidget

A CLI video downloader built on [yt-dlp](https://github.com/yt-dlp/yt-dlp) — a local
replacement for iTube Studio supporting 1000+ sites including Fox News, YouTube, Twitter/X,
and any HLS/Brightcove stream.

## Features

- Download video + audio from 1000+ sites via yt-dlp
- Select quality (best, 1080p, 720p, 480p, 360p, audio-only)
- Select output format (mp4, mkv, webm, mp3, m4a)
- Batch download from a URLs text file
- Live Rich progress bar with speed and ETA
- Persistent config at `~/.vidget/config.json`
- Subtitle download support
- Retry logic with back-off on network failures

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (package manager)
- [ffmpeg](https://ffmpeg.org/) — required for format conversion and HLS stream merging

```bash
brew install ffmpeg  # macOS
```

## Install

```bash
git clone https://github.com/jreakin/jre-vidget.git
cd jre-vidget
bash install.sh
```

Or manually:

```bash
uv sync --extra dev
```

With pip (editable install and dev tools):

```bash
pip install -e ".[dev]"
```

## Usage

**Phase 1 (scaffold):** a single stub command accepts a URL and prints a placeholder message.

```bash
vidget --help
vidget https://example.com
```

**Planned CLI surface** (later phases):

```bash
vidget <url>
vidget batch <file>
vidget formats <url>
vidget config show
vidget config set --output ~/Videos --quality 1080p --format mp4
```

Examples after the Typer CLI is fully wired (see `prompts/phase-4-typer-cli/`):

```bash
# Download a video (best quality, mp4)
vidget download https://www.foxnews.com/video/6390070137112

# Download 720p as mp3 to a specific folder
vidget download https://youtube.com/watch?v=... --quality 720p --format mp3 --output ~/Music

# List available formats for a URL
vidget formats https://www.foxnews.com/video/6390070137112

# Batch download from a file (one URL per line, # for comments)
vidget batch urls.txt --output ~/Downloads/videos

# View / edit config
vidget config show
vidget config set --quality 720p --format mp4
vidget config reset --yes

# Version
vidget --version
```

## Development

```bash
uv run pytest                    # Run tests
uv run ruff check src/           # Lint
uv run mypy src/ --strict        # Type check
```

## Implementation

This tool is built in phases. See the `prompts/` directory for the phase-by-phase
implementation guide designed for AI coding agents:

| Phase | File | Covers |
|-------|------|--------|
| 1 | `prompts/phase-1-project-scaffold.md` | Project setup, folder structure |
| 2 | `prompts/phase-2-pydantic-models.md` | Data models |
| 3 | `prompts/phase-3-download-engine.md` | yt-dlp wrapper |
| 4 | `prompts/phase-4-typer-cli.md` | CLI commands |
| 5 | `prompts/phase-5-rich-ui.md` | Rich terminal UI |
| 6 | `prompts/phase-6-config-error-polish.md` | Error handling & polish |

## License

MIT
