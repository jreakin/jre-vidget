# jre-vidget

A self-hosted video downloader and YouTube publisher. Fork this repo, configure your credentials, and get a personal web UI at `https://YOUR_USERNAME.github.io/jre-vidget/` — no server, no subscription, no install. GitHub Actions does the work.

## Deploy in 5 minutes

1. **Fork** this repo
2. **Add your secrets** — from your local terminal (requires [GitHub CLI](https://cli.github.com/)):
   ```bash
   gh auth login          # if not already authenticated
   git clone https://github.com/YOUR_USERNAME/jre-vidget && cd jre-vidget
   bash scripts/setup-secrets.sh
   ```
   This creates placeholder entries in Settings → Secrets → Actions. Click each one and replace `REPLACE_ME — ...` with your real credential. See [docs/SETUP.md](docs/SETUP.md) for where to get each value.
3. Go to **Actions** → **Bootstrap** → **Run workflow** — sets repo variables and verifies all secrets are filled in
4. Go to **Settings** → **Pages** → source: **Deploy from a branch** → branch: **gh-pages**
5. Your web UI is live at `https://YOUR_USERNAME.github.io/jre-vidget/`

### YouTube / Google OAuth (web UI)

The Pages app does **not** complete Google sign-in inside the static site. YouTube uploads run in **GitHub Actions**, which read `VIDGET_CLIENT_ID`, `VIDGET_CLIENT_SECRET`, and `VIDGET_REFRESH_TOKEN` from repository secrets (the in-browser setup wizard can write those secrets if your GitHub PAT allows it).

1. In [Google Cloud Console](https://console.cloud.google.com/), enable **YouTube Data API v3**, finish the **OAuth consent screen**, then create an **OAuth 2.0 Client ID** with application type **Desktop app** (this matches `vidget auth login`, which uses a localhost redirect).
2. On your computer, run `uv run vidget auth login` once, then copy the refresh token from `~/.vidget/config.json` into the secret `VIDGET_REFRESH_TOKEN` (or paste it in the setup wizard).

Full walkthrough (scopes, test users, optional `VIDGET_OAUTH_PORT`, and GitHub secret names): **[docs/SETUP.md](docs/SETUP.md)** — [Step 2: Google Cloud OAuth client](docs/SETUP.md#step-2) and [Step 3: Refresh token](docs/SETUP.md#step-3).

## How it works

```
Web UI (GitHub Pages)
  → paste URL, click Download or Publish
  → triggers a GitHub Actions workflow
  → runner installs yt-dlp + ffmpeg, downloads the video
  → optionally uploads to your YouTube channel via the YouTube Data API
  → web UI shows status and history
```

You don't install anything. yt-dlp, ffmpeg, and Python all run on GitHub's free CI runners. Your credentials stay in GitHub Secrets — never in the repo. If you use the browser UI with a GitHub PAT, read the **Web UI: GitHub PAT** risk section in [docs/SETUP.md](docs/SETUP.md) (localStorage scope and XSS considerations).

## Features

- Download from 1000+ sites via yt-dlp (Fox News, YouTube, Twitter/X, HLS streams, …)
- Publish directly to YouTube with title, description, and privacy controls
- Preview metadata (title, duration, thumbnail) before committing to an upload
- Quality presets: best, 1080p, 720p, 480p, 360p, audio-only
- Output formats: mp4, mkv, webm, mp3, m4a
- Batch downloads from a URL list
- Download history in the web UI

## Status & quality

[![CI](https://img.shields.io/github/actions/workflow/status/jreakin/jre-vidget/ci.yml?branch=main&logo=github&label=CI)](https://github.com/jreakin/jre-vidget/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/jreakin/jre-vidget)](https://github.com/jreakin/jre-vidget/blob/main/LICENSE)
[![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fjreakin%2Fjre-vidget%2Fmain%2Fpyproject.toml&logo=python&logoColor=white)](https://github.com/jreakin/jre-vidget/blob/main/pyproject.toml)
[![Release](https://img.shields.io/github/v/release/jreakin/jre-vidget?logo=github&sort=semver)](https://github.com/jreakin/jre-vidget/releases)
[![Last commit](https://img.shields.io/github/last-commit/jreakin/jre-vidget?logo=git&logoColor=white)](https://github.com/jreakin/jre-vidget/commits/main/)

[![pytest](https://img.shields.io/pypi/v/pytest?logo=pytest&logoColor=white&label=pytest)](https://docs.pytest.org/)
[![Coverage](https://img.shields.io/badge/coverage-pytest--cov-informational?logo=pytest&logoColor=white)](https://github.com/jreakin/jre-vidget/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/pypi/v/ruff?logo=ruff&logoColor=D7FF64&label=ruff)](https://docs.astral.sh/ruff/)
[![ty](https://img.shields.io/pypi/v/ty?label=ty&logo=python&logoColor=white)](https://docs.astral.sh/ty/)

Line coverage is produced on every CI run; pull requests get a comment with totals and a comparison to `main`.

## Stack

[![Typer](https://img.shields.io/pypi/v/typer?logo=python&logoColor=white&label=Typer)](https://typer.tiangolo.com/)
[![Rich](https://img.shields.io/pypi/v/rich?logo=rich&label=Rich)](https://rich.readthedocs.io/)
[![Pydantic](https://img.shields.io/pypi/v/pydantic?logo=pydantic&logoColor=white&label=Pydantic)](https://docs.pydantic.dev/)
[![yt-dlp](https://img.shields.io/pypi/v/yt-dlp?logo=youtube&logoColor=white&label=yt-dlp)](https://github.com/yt-dlp/yt-dlp)
[![ffmpeg-python](https://img.shields.io/pypi/v/ffmpeg-python?logo=ffmpeg&logoColor=white&label=ffmpeg-python)](https://github.com/kkroening/ffmpeg-python)
[![uv](https://img.shields.io/pypi/v/uv?logo=uv&logoColor=white&label=uv)](https://docs.astral.sh/uv/)
[![Hatchling](https://img.shields.io/pypi/v/hatchling?logo=hatch&logoColor=white&label=hatchling)](https://hatch.pypa.io/latest/build/)

## Local CLI (optional)

If you want to run downloads locally instead of through GitHub Actions, the CLI is packaged as a Docker image — no Python or ffmpeg install required on your host.

```bash
# Build the image once after cloning
make setup

# Download a single video (lands in ./downloads/ by default)
make download URL="https://www.foxnews.com/video/6390070137112"
make download URL="https://youtube.com/watch?v=…" OUTPUT=~/Videos

# Batch download from a text file (one URL per line, # for comments)
make batch FILE=urls.txt

# List available formats without downloading
make formats URL="https://www.foxnews.com/video/6390070137112"
```

Or run Docker directly:

```bash
docker run --rm -v ~/Downloads:/downloads jre-vidget download "https://..." --output /downloads
```

## Development

Requirements: [Docker Desktop](https://www.docker.com/products/docker-desktop/), Python 3.11+, [uv](https://docs.astral.sh/uv/), and ffmpeg (`brew install ffmpeg` on macOS).

```bash
git clone https://github.com/jreakin/jre-vidget.git
cd jre-vidget
uv sync --extra dev
make setup-hooks   # wires .githooks/commit-msg — enforces conventional commit format
```

| Make target | What it runs |
|-------------|----------------|
| `make dev` | `uv sync --extra dev` |
| `make setup-hooks` | Wire `.githooks/` as the local git hooks path |
| `make test` | Full pytest suite |
| `make test-unit` / `make test-integration` | Focused test paths |
| `make coverage` | Pytest with `--cov=src` and missing lines |
| `make lint` | Ruff check + [ty](https://docs.astral.sh/ty/) on `src/` and `tests/` |
| `make format` / `make format-check` | Ruff format (write / verify) |
| `make all` | CI-equivalent: format-check, lint, test |

CI runs **quality** (ruff, ty) and **tests** (pytest, coverage) on Python 3.12 and 3.13 via reusable workflows under [`.github/workflows/`](https://github.com/jreakin/jre-vidget/tree/main/.github/workflows).

## Implementation phases

Built in ordered phases; each prompt's `current.md` is the source of truth for agents:

| Phase | Prompt | Topics |
|-------|--------|--------|
| 1 | [`prompts/phase-1-project-scaffold/current.md`](prompts/phase-1-project-scaffold/current.md) | Layout, packaging, stub CLI |
| 2 | [`prompts/phase-2-pydantic-models/current.md`](prompts/phase-2-pydantic-models/current.md) | Pydantic models |
| 3 | [`prompts/phase-3-download-engine/current.md`](prompts/phase-3-download-engine/current.md) | yt-dlp engine |
| 4 | [`prompts/phase-4-typer-cli/current.md`](prompts/phase-4-typer-cli/current.md) | Typer commands |
| 5 | [`prompts/phase-5-rich-ui/current.md`](prompts/phase-5-rich-ui/current.md) | Rich UI |
| 6 | [`prompts/phase-6-config-error-polish/current.md`](prompts/phase-6-config-error-polish/current.md) | Checks, polish, exits |
| 15 | [`prompts/phase-15-metadata-preview/current.md`](prompts/phase-15-metadata-preview/current.md) | Metadata preview before upload |

See [`AGENTS.md`](AGENTS.md) for agent workflows, exit codes, and conventions.

## License

MIT
