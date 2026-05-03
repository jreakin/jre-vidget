# jre-vidget

A CLI video downloader built on [yt-dlp](https://github.com/yt-dlp/yt-dlp) — a local replacement for iTube Studio supporting 1000+ sites including Fox News, YouTube, Twitter/X, and many HLS/Brightcove streams.

## Status & quality

[![CI](https://img.shields.io/github/actions/workflow/status/jreakin/jre-vidget/ci.yml?branch=main&logo=github&label=CI)](https://github.com/jreakin/jre-vidget/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/jreakin/jre-vidget)](https://github.com/jreakin/jre-vidget/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://github.com/jreakin/jre-vidget/blob/main/pyproject.toml)
[![Release](https://img.shields.io/github/v/release/jreakin/jre-vidget?logo=github)](https://github.com/jreakin/jre-vidget/releases)

[![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)](https://github.com/jreakin/jre-vidget/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-pytest--cov-informational?logo=pytest&logoColor=white)](https://github.com/jreakin/jre-vidget/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/badge/ruff-lint%20%2B%20format-281E32?logo=ruff&logoColor=D7FF64)](https://docs.astral.sh/ruff/)
[![mypy](https://img.shields.io/badge/mypy-strict-2B5EA8?logo=mypy&logoColor=white)](https://mypy-lang.org/)

Line coverage is produced on every CI run (`coverage.json`); pull requests get a [CI report workflow](https://github.com/jreakin/jre-vidget/blob/main/.github/workflows/ci-report.yml) comment with totals and comparison to `main`.

## Stack

Runtime and packaging ([Shields.io](https://shields.io/) static badges):

[![Typer](https://img.shields.io/badge/Typer-CLI-7C3AED?logo=python&logoColor=white)](https://typer.tiangolo.com/)
[![Rich](https://img.shields.io/badge/Rich-terminal%20UI-FFAA00?logo=rich&logoColor=black)](https://rich.readthedocs.io/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![yt--dlp](https://img.shields.io/badge/yt--dlp-downloads-248077?logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![ffmpeg--python](https://img.shields.io/badge/ffmpeg--python-wrapper-007808?logo=ffmpeg&logoColor=white)](https://github.com/kkroening/ffmpeg-python)
[![uv](https://img.shields.io/badge/uv-astral-7056BF?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![Hatchling](https://img.shields.io/badge/build-hatchling-3775A9?logo=hatch&logoColor=white)](https://hatch.pypa.io/latest/build/)

External binary: **[ffmpeg](https://ffmpeg.org/)** on your PATH for conversion and HLS merge.

## Features

- Download video and audio from 1000+ sites via yt-dlp
- Quality presets (best, 1080p, 720p, 480p, 360p, audio-only)
- Output formats (mp4, mkv, webm, mp3, m4a, …)
- Batch download from a text file (one URL per line, `#` comments)
- Rich progress bar with speed and ETA
- Persistent config at `~/.vidget/config.json`
- Optional subtitles
- Retries with backoff on transient engine errors

## Requirements

<<<<<<< New base: Project: add CLI stub, docs, Makefile, and packaging changes
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- [ffmpeg](https://ffmpeg.org/) — format conversion and stream merging
||||||| Common ancestor
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager)
- [ffmpeg](https://ffmpeg.org/) — required for format conversion and HLS stream merging
=======
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (package manager)
- [ffmpeg](https://ffmpeg.org/) — required for format conversion and HLS stream merging
>>>>>>> Current commit: Project: add CLI stub, docs, Makefile, and packaging changes

```bash
brew install ffmpeg  # macOS
```

## Install

```bash
git clone https://github.com/jreakin/jre-vidget.git
cd jre-vidget
bash install.sh
```

Or with uv:

```bash
uv sync --extra dev
```

<<<<<<< New base: Project: add CLI stub, docs, Makefile, and packaging changes
Editable install with dev tools via pip:

```bash
pip install -e ".[dev]"
```

The `vidget` command is provided by the `jre-vidget` package ([`pyproject.toml`](https://github.com/jreakin/jre-vidget/blob/main/pyproject.toml) script entry).

||||||| Common ancestor
=======
With pip (editable install and dev tools):

```bash
pip install -e ".[dev]"
```

>>>>>>> Current commit: Project: add CLI stub, docs, Makefile, and packaging changes
## Usage

<<<<<<< New base: Project: add CLI stub, docs, Makefile, and packaging changes
Dependency checks (yt-dlp importable, ffmpeg on PATH) run automatically before commands other than `config`.

||||||| Common ancestor
=======
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

>>>>>>> Current commit: Project: add CLI stub, docs, Makefile, and packaging changes
```bash
vidget --help
vidget --version

# Download (uses saved defaults from config when flags are omitted)
vidget download https://www.foxnews.com/video/6390070137112
vidget download 'https://youtube.com/watch?v=…' --quality 720p --format mp3 --output ~/Music

# Inspect formats
vidget formats https://www.foxnews.com/video/6390070137112

# Batch file: one URL per line, # starts a comment
vidget batch urls.txt --output ~/Downloads/videos

# Config
vidget config show
vidget config set --quality 720p --format mp4 --output ~/Videos
vidget config reset --yes
```

## Development

| Make target | What it runs |
|-------------|----------------|
| `make dev` | `uv sync --extra dev` |
| `make test` | Full pytest suite |
| `make test-unit` / `make test-integration` | Focused test paths |
| `make coverage` | Pytest with `--cov=src` and missing lines |
| `make lint` | Ruff check + mypy on `src/` |
| `make format` / `make format-check` | Ruff format (write / verify) |
| `make typecheck` | mypy only |
| `make all` | CI-equivalent: format-check, lint, test |

Equivalent with uv:

```bash
uv run pytest
uv run pytest --cov=src --cov-report=term-missing
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/ --strict
```

CI (GitHub Actions) runs **quality** (ruff check, ruff format `--check`, mypy) and **tests** (pytest with coverage) on Python 3.12 and 3.13 via the reusable workflows under [`.github/workflows/`](https://github.com/jreakin/jre-vidget/tree/main/.github/workflows).

## Implementation phases

Built in ordered phases; each prompt’s `current.md` is the source of truth for agents:

| Phase | Prompt | Topics |
|-------|--------|--------|
| 1 | [`prompts/phase-1-project-scaffold/current.md`](prompts/phase-1-project-scaffold/current.md) | Layout, packaging, stub CLI |
| 2 | [`prompts/phase-2-pydantic-models/current.md`](prompts/phase-2-pydantic-models/current.md) | Pydantic models |
| 3 | [`prompts/phase-3-download-engine/current.md`](prompts/phase-3-download-engine/current.md) | yt-dlp engine |
| 4 | [`prompts/phase-4-typer-cli/current.md`](prompts/phase-4-typer-cli/current.md) | Typer commands |
| 5 | [`prompts/phase-5-rich-ui/current.md`](prompts/phase-5-rich-ui/current.md) | Rich UI |
| 6 | [`prompts/phase-6-config-error-polish/current.md`](prompts/phase-6-config-error-polish/current.md) | Checks, polish, exits |

See [`AGENTS.md`](AGENTS.md) for agent workflows, exit codes, and conventions.

## License

MIT
