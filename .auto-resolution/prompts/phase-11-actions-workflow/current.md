# Phase 11 — GitHub Actions Publish Workflow
# Version: 0.1.0
# Model: claude-sonnet-4-6
# Last Updated: 2026-05-03
# Maintainer: jreakin
# Status: Draft

---

## Goal

Wire the YouTube publish feature into GitHub Actions so any cloner can trigger a
download-and-upload job from their browser without running anything locally. Adds
`VIDGET_REFRESH_TOKEN` env var support to `auth.py`, creates the
`workflow_dispatch`-triggered publish workflow, writes upload records to
`uploads.json` so the web UI (Phase 12) can display history, and documents the
one-time OAuth setup.

---

## Spec Reference

`docs/superpowers/specs/2026-05-03-youtube-publish-design.md`

---

## Prerequisites

- Phases 7–10 complete (models, auth, publisher, CLI all working)
- Google Cloud project with YouTube Data API v3 enabled
- OAuth 2.0 Desktop App credentials created (client_id + client_secret)
- `vidget auth login` run locally at least once to obtain a refresh_token

---

## Files

| Action | File |
|--------|------|
| Modify | `src/jre_vidget/auth.py` |
| Modify | `tests/unit/test_auth.py` |
| Create | `.github/workflows/publish.yml` |
| Create | `uploads.json` |
| Create | `docs/SETUP.md` |

---

## Implementation

### Step 1 — Write failing tests for VIDGET_REFRESH_TOKEN

Add to `tests/unit/test_auth.py` inside `TestGetCredentials`:

```python
def test_env_var_refresh_token_overrides_config(self, monkeypatch):
    """VIDGET_REFRESH_TOKEN env var takes precedence over AuthConfig.refresh_token."""
    monkeypatch.setenv("VIDGET_REFRESH_TOKEN", "env-refresh-token")
    auth = AuthConfig(
        client_id="cid",
        client_secret="csecret",
        refresh_token="config-token",
    )
    mock_creds = MagicMock()
    mock_creds.valid = True

    with patch("jre_vidget.auth.Credentials") as mock_creds_cls:
        mock_creds_cls.return_value = mock_creds
        get_credentials(auth)

    _, kwargs = mock_creds_cls.call_args
    assert kwargs["refresh_token"] == "env-refresh-token"

def test_env_var_refresh_token_allows_empty_config(self, monkeypatch):
    """All three env vars set → AuthConfig can be completely empty."""
    monkeypatch.setenv("VIDGET_REFRESH_TOKEN", "env-rt")
    monkeypatch.setenv("VIDGET_CLIENT_ID", "env-cid")
    monkeypatch.setenv("VIDGET_CLIENT_SECRET", "env-csecret")

    mock_creds = MagicMock()
    mock_creds.valid = True

    with patch("jre_vidget.auth.Credentials") as mock_creds_cls:
        mock_creds_cls.return_value = mock_creds
        get_credentials(AuthConfig())  # no config values at all — should not raise

    _, kwargs = mock_creds_cls.call_args
    assert kwargs["refresh_token"] == "env-rt"
    assert kwargs["client_id"] == "env-cid"
    assert kwargs["client_secret"] == "env-csecret"
```

Run — confirm both fail:
```bash
uv run pytest tests/unit/test_auth.py::TestGetCredentials::test_env_var_refresh_token_overrides_config \
              tests/unit/test_auth.py::TestGetCredentials::test_env_var_refresh_token_allows_empty_config -v
```
Expected: FAIL — `auth.py` doesn't read `VIDGET_REFRESH_TOKEN` yet.

---

### Step 2 — Update `auth.py` to read VIDGET_REFRESH_TOKEN

In `get_credentials`, add the env var lookup for `refresh_token` alongside the
existing lookups for `client_id` and `client_secret`:

```python
def get_credentials(auth: AuthConfig) -> Credentials:
    client_id = os.getenv("VIDGET_CLIENT_ID") or auth.client_id
    client_secret = os.getenv("VIDGET_CLIENT_SECRET") or auth.client_secret
    refresh_token = os.getenv("VIDGET_REFRESH_TOKEN") or auth.refresh_token  # ← add

    if not refresh_token or not client_id or not client_secret:
        raise AuthError(
            "Not authenticated. Run 'vidget auth login' to connect your YouTube account."
        )

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,   # ← use resolved value (not auth.refresh_token)
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )

    if not creds.valid:
        if creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError as e:
                raise AuthError(
                    "YouTube session expired. Run 'vidget auth login' to reconnect."
                ) from e

    return creds
```

---

### Step 3 — Run auth tests

```bash
uv run pytest tests/unit/test_auth.py -v
```
Expected: all tests **PASS**.

---

### Step 4 — Create `uploads.json`

Create at the repo root:

```json
{
  "uploads": []
}
```

This file is committed to `main`. The publish workflow appends a record after each
successful upload and pushes the update back.

---

### Step 5 — Create `.github/workflows/publish.yml`

```yaml
name: Download & publish to YouTube

on:
  workflow_dispatch:
    inputs:
      url:
        description: "Video URL to download"
        required: true
        type: string
      title:
        description: "YouTube title (leave blank to use scraped title)"
        required: false
        type: string
        default: ""
      description:
        description: "YouTube description"
        required: false
        type: string
        default: ""
      privacy:
        description: "Privacy setting"
        required: false
        type: choice
        default: "public"
        options:
          - public
          - unlisted
          - private
      remove_after_upload:
        description: "Delete local file after successful upload"
        required: false
        type: boolean
        default: false

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: write   # needed to push uploads.json update

    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Install system dependencies
        run: sudo apt-get update && sudo apt-get install -y --no-install-recommends ffmpeg

      - name: Set up uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Install project
        run: uv sync

      - name: Download & publish
        id: publish
        env:
          VIDGET_CLIENT_ID: ${{ secrets.VIDGET_CLIENT_ID }}
          VIDGET_CLIENT_SECRET: ${{ secrets.VIDGET_CLIENT_SECRET }}
          VIDGET_REFRESH_TOKEN: ${{ secrets.VIDGET_REFRESH_TOKEN }}
        run: |
          TITLE_FLAG=""
          if [ -n "${{ inputs.title }}" ]; then
            TITLE_FLAG="--title ${{ inputs.title }}"
          fi

          REMOVE_FLAG=""
          if [ "${{ inputs.remove_after_upload }}" = "true" ]; then
            REMOVE_FLAG="--remove"
          fi

          OUTPUT=$(uv run vidget download "${{ inputs.url }}" \
            --publish \
            $TITLE_FLAG \
            --description "${{ inputs.description }}" \
            --privacy "${{ inputs.privacy }}" \
            $REMOVE_FLAG 2>&1)

          echo "$OUTPUT"

          VIDEO_ID=$(echo "$OUTPUT" | grep -oP 'watch\?v=\K[A-Za-z0-9_-]+' | head -1)
          echo "video_id=$VIDEO_ID" >> "$GITHUB_OUTPUT"
          echo "output=$OUTPUT" >> "$GITHUB_OUTPUT"

      - name: Update uploads.json
        if: steps.publish.outputs.video_id != ''
        run: |
          python3 - <<'EOF'
          import json, os, datetime

          path = "uploads.json"
          with open(path) as f:
              data = json.load(f)

          video_id = "${{ steps.publish.outputs.video_id }}"
          title = "${{ inputs.title }}" or "untitled"
          record = {
              "video_id": video_id,
              "url": f"https://youtube.com/watch?v={video_id}",
              "title": title,
              "source_url": "${{ inputs.url }}",
              "privacy": "${{ inputs.privacy }}",
              "uploaded_at": datetime.datetime.utcnow().isoformat() + "Z",
              "run_id": "${{ github.run_id }}",
          }
          data["uploads"].insert(0, record)

          with open(path, "w") as f:
              json.dump(data, f, indent=2)
          EOF

      - name: Commit uploads.json
        if: steps.publish.outputs.video_id != ''
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add uploads.json
          git diff --staged --quiet || git commit -m "chore: record upload ${{ steps.publish.outputs.video_id }}"
          git push
```

---

### Step 6 — Create `docs/SETUP.md`

```markdown
# Setup Guide

## Prerequisites

1. A Google Cloud project with **YouTube Data API v3** enabled
2. OAuth 2.0 credentials (type: **Desktop App**) — copy the client ID and secret
3. [uv](https://docs.astral.sh/uv/) installed locally for the one-time auth step

## One-time OAuth flow (local)

Run this once on your machine to obtain a refresh token:

```bash
git clone https://github.com/YOUR_USERNAME/jre-vidget
cd jre-vidget
uv sync
uv run vidget auth login
# → enter your client ID and client secret when prompted
# → browser opens, sign in to Google, grant access
# → token saved to ~/.vidget/config.json
```

Then extract the refresh token:
```bash
python3 -c "
import json, pathlib
cfg = json.loads(pathlib.Path.home().joinpath('.vidget/config.json').read_text())
print('VIDGET_CLIENT_ID    =', cfg['auth']['client_id'])
print('VIDGET_CLIENT_SECRET=', cfg['auth']['client_secret'])
print('VIDGET_REFRESH_TOKEN=', cfg['auth']['refresh_token'])
"
```

## GitHub Secrets

Add these four secrets to your repo
(**Settings → Secrets and variables → Actions → New repository secret**):

| Secret name            | Value                            |
|------------------------|----------------------------------|
| `VIDGET_CLIENT_ID`     | From Google Cloud Console        |
| `VIDGET_CLIENT_SECRET` | From Google Cloud Console        |
| `VIDGET_REFRESH_TOKEN` | From `~/.vidget/config.json`     |
| `VIDGET_REPORT_TOKEN`  | See Phase 13 — error reporting   |

## GitHub Variables (non-sensitive)

Add these under **Settings → Secrets and variables → Actions → Variables**:

| Variable name    | Example value          | Purpose                  |
|------------------|------------------------|--------------------------|
| `VITE_APP_TITLE` | `JRE Clip Uploader`    | Title shown in the web UI |
| `VITE_GITHUB_REPO` | `jreakin/jre-vidget` | Repo the UI targets      |

## Triggering a job

- **From the web UI**: see Phase 12
- **From GitHub**: Actions tab → "Download & publish to YouTube" → Run workflow

## Refreshing an expired token

If you see `YouTube session expired` in a workflow run, repeat the
one-time OAuth flow above and update the `VIDGET_REFRESH_TOKEN` secret.
```

---

### Step 7 — Type check and lint

```bash
uv run mypy src/jre_vidget/auth.py --strict
uv run ruff check src/jre_vidget/auth.py
```
Expected: no errors.

---

### Step 8 — Commit

```bash
git add src/jre_vidget/auth.py \
        tests/unit/test_auth.py \
        .github/workflows/publish.yml \
        uploads.json \
        docs/SETUP.md
git commit -m "feat: add Actions publish workflow and VIDGET_REFRESH_TOKEN env var"
```

---

## Acceptance Criteria

- [ ] `get_credentials` reads `VIDGET_REFRESH_TOKEN` from env, overriding `AuthConfig.refresh_token`
- [ ] `AuthConfig()` with all fields `None` works when all three env vars are set
- [ ] All existing `test_auth.py` tests still pass
- [ ] `.github/workflows/publish.yml` triggers on `workflow_dispatch` with `url`, `title`, `description`, `privacy`, `remove_after_upload` inputs
- [ ] Workflow installs ffmpeg and uv, runs `vidget download --publish`
- [ ] Workflow extracts `video_id` from CLI output and writes a record to `uploads.json`
- [ ] Workflow commits and pushes `uploads.json` after each successful upload
- [ ] `docs/SETUP.md` documents the full one-time setup including secret extraction
- [ ] `mypy --strict` clean on `auth.py`
