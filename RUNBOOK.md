# RUNBOOK.md
# Operational quick reference for jre-vidget
# Last Updated: 2026-05-03

---

## Development Setup

```bash
# First-time setup
git clone <repo> && cd jre-vidget
brew install ffmpeg          # Required for HLS merge + format conversion
uv sync --extra dev          # Install all dependencies including dev extras
uv run vidget --help         # Verify entry point works
```

---

## Common Commands

```bash
# Install / sync
uv sync                      # Sync deps from lockfile
uv sync --extra dev          # Include dev extras (pytest, ruff, mypy)
uv run vidget --version      # Check installed version

# Test
uv run pytest                # Full suite
uv run pytest tests/unit -x  # Unit only, stop on first failure
uv run pytest -v --cov=src --cov-report=term-missing  # With coverage

# Lint / format / type-check
uv run ruff check src/       # Lint
uv run ruff format src/      # Format
uv run ruff check src/ --fix # Auto-fix safe issues
uv run mypy src/ --strict    # Type check

# Run a smoke test against a real URL (requires network + ffmpeg)
uv run vidget formats https://www.foxnews.com/video/6390070137112
```

---

## Common Issues & Fixes

### Issue: `vidget: command not found` after `uv sync`

**Diagnosis:** Entry point not installed into the venv.

```bash
uv run which vidget          # Should show .venv/bin/vidget
uv pip install -e .          # Re-install in editable mode
```

**Fix:** Ensure `pyproject.toml` has `[project.scripts] vidget = "jre_vidget.cli:app"` and run `uv sync`.

---

### Issue: `ModuleNotFoundError: No module named 'jre_vidget'`

**Diagnosis:** Package not installed or wrong Python.

```bash
uv run python -c "import jre_vidget; print(jre_vidget.__file__)"
```

**Fix:** Run `uv sync` then `uv pip install -e .`

---

### Issue: `ffmpeg not found` warning on startup

**Diagnosis:** ffmpeg is not on PATH.

```bash
which ffmpeg                 # Should return a path
brew install ffmpeg          # macOS fix
```

Note: This is a warning, not fatal. Downloading without format conversion still works.

---

### Issue: `yt-dlp not found` error on startup

**Diagnosis:** yt-dlp not installed in the active venv.

```bash
uv run python -c "import yt_dlp; print(yt_dlp.version.__version__)"
uv sync                      # Should install it
```

---

### Issue: pytest import errors on `from jre_vidget.cli import app`

**Diagnosis:** `src/` layout not on sys.path.

```bash
# Check pyproject.toml has [tool.pytest.ini_options] testpaths = ["tests"]
# Verify package is installed editable:
uv pip install -e .
```

---

### Issue: HLS video downloads as audio-only or misses video track

**Diagnosis:** yt-dlp format selector not merging streams; ffmpeg missing.

```bash
uv run vidget formats <url>   # Inspect available formats
which ffmpeg                  # Must be present for merging
```

**Fix:** Install ffmpeg. Use `--quality best` which triggers `bestvideo+bestaudio/best`.

---

### Issue: `mypy src/ --strict` fails with `error: Cannot find implementation...`

**Diagnosis:** Missing `py.typed` marker or stubs.

```bash
# Add to src/jre_vidget/__init__.py:
# (empty file is fine, but needs to exist)
touch src/jre_vidget/py.typed
```

---

## Debug Commands

```bash
# Check yt-dlp version
uv run python -c "import yt_dlp; print(yt_dlp.version.__version__)"

# Probe a URL without downloading (raw yt-dlp output)
uv run python -c "
import yt_dlp, json
with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
    info = ydl.extract_info('https://www.foxnews.com/video/6390070137112', download=False)
    print(info['title'], '—', len(info.get('formats', [])), 'formats')
"

# List all installed entry points
uv run python -c "
from importlib.metadata import entry_points
for ep in entry_points(group='console_scripts'):
    if 'vidget' in ep.name:
        print(ep)
"

# Run a single test with full output
uv run pytest tests/unit/test_models.py::test_quality_ydl_format -v -s
```

---

## GitHub Actions publish (`publish.yml`)

The workflow runs `vidget auth status --strict` before download so missing or blank
`VIDGET_CLIENT_ID`, `VIDGET_CLIENT_SECRET`, or `VIDGET_REFRESH_TOKEN` fails fast (exit code 3)
instead of halfway through an upload.

**What `--strict` does not do:** it does **not** call Google’s token endpoint. It only
confirms the three values are present after merging env vars and `~/.vidget/config.json`.
A revoked refresh token or disabled API can still make the next step fail with an auth
or quota error—see below.

### YouTube Data API quota and failures

Uploads use the [YouTube Data API v3](https://developers.google.com/youtube/v3/getting-started#quota).
Each upload consumes quota; daily project caps can cause `quotaExceeded` or rate-style errors.
If CI publish fails after auth succeeds, check [Google Cloud Console](https://console.cloud.google.com/)
for API usage and quota, and confirm the OAuth project has **YouTube Data API v3** enabled.
Refresh tokens can be revoked in Google Account security settings; treat `invalid_grant` as
“re-run `vidget auth login` locally and update `VIDGET_REFRESH_TOKEN` in repository secrets.”

## CI / Release

```bash
# Trigger CI manually (requires gh CLI)
gh workflow run ci.yml

# Check latest CI status
gh run list --workflow=ci.yml --limit=5

# Create a release PR (release-please handles this automatically on push to main)
# Conventional commit message examples:
#   feat: add subtitle download support
#   fix: handle missing ffmpeg gracefully
#   chore: update yt-dlp to 2025.x
```
