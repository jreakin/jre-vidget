# NOTES.md
# Cross-session context for jre-vidget

Cross-platform facts and session notes. Read this at the start of any session to
avoid rediscovering context already earned.

---

## Platform & Environment

- **Development machine:** macOS (arm64). `tmp/` in repo root is used for local
  CLI smoke tests — it's in `.gitignore`, so artifacts stay out of version control.
- **Python:** 3.11 (pinned in `.python-version`). Managed via `uv`.
- **ffmpeg** must be on `PATH` for downloads requiring stream merge (HLS/DASH).
  Install via `brew install ffmpeg` on macOS; the CI matrix installs it via apt.
- **yt-dlp** is a Python package dependency, not a system binary.

---

## YouTube OAuth Setup

YouTube Data API v3 write operations (uploads) require three credentials:

| Variable | Source |
|----------|--------|
| `GCLOUD_CLIENT_ID` | Google Cloud Console → OAuth 2.0 Desktop App client ID (primary) |
| `GCLOUD_AUTH_CLIENT_ID` | Optional second client-ID secret (same app if you use two slots) |
| `GCLOUD_CLIENT_SECRET` / `VIDGET_CLIENT_SECRET` | OAuth client secret |
| `GCLOUD_REFRESH_TOKEN` / `VIDGET_REFRESH_TOKEN` | Run `vidget auth login` locally; copy from `~/.vidget/config.json` |

These are stored as GitHub Actions secrets. See `docs/SETUP.md` for step-by-step instructions.
`VIDGET_REPORT_TOKEN` is a separate fine-grained GitHub token with `issues: write` only on
`jreakin/jre-vidget` — it lets the publish workflow auto-report failures to the upstream repo.

---

## Web UI

The `web/` directory is a Vite + React + TanStack (Query + Router) app, deployed to the
`gh-pages` branch via `.github/workflows/deploy-web.yml`. It is a **static site** — no server.

- `VITE_GITHUB_REPO` and `VITE_APP_TITLE` are baked in at build time via Vite env vars.
- GitHub PAT is stored in `localStorage` on first visit (personal tool pattern).
- `uploads.json` at the repo root is the upload history; the web UI reads it via raw GitHub URL.

---

## Repo Deployment Path

```
main branch push → ci.yml (lint + tests)
web/** push      → deploy-web.yml (build React app → push to gh-pages branch)
workflow_dispatch → publish.yml (download + YouTube upload → append uploads.json → push)
workflow_dispatch → bootstrap.yml (scaffold secrets/variables for cloners)
```

---

## Known Constraints

- `engine.py` must **never** import from `ui.py` — engine is pure business logic.
- `publisher.py` must **never** be called from `engine.py` — it goes through `cli.py`.
- Tests that hit the YouTube API must mock `googleapiclient.discovery.build` at the boundary.
- The `next_chunk()` loop pattern (not `.execute()`) is used for resumable YouTube uploads.
- `Credentials(token=None)` starts with `valid=False` but `expired=False` — the refresh
  condition checks `creds.refresh_token`, not `creds.expired`.

---

## Useful One-Liners

```bash
# Extract credentials after running vidget auth login
python3 -c "import json,pathlib; c=json.loads(pathlib.Path.home().joinpath('.vidget/config.json').read_text())['auth']; print(c['client_id'], c['client_secret'], c['refresh_token'])"

# Build and preview the web UI locally
cd web && npm run dev
```
