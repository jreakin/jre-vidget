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
| `VIDGET_REPORT_TOKEN`  | Optional — see below               |

### Creating the `VIDGET_REPORT_TOKEN`

This token lets the publish workflow automatically report failures to the upstream
repo so the maintainer can fix them. It has the minimum possible permissions.

1. Go to **GitHub → Settings → Developer settings → Fine-grained tokens → Generate new token**
2. Set:
   - **Token name:** `vidget-error-reporter`
   - **Expiration:** 1 year (or no expiration)
   - **Resource owner:** your account
   - **Repository access:** Only select repositories → `jreakin/jre-vidget`
   - **Permissions:** Repository permissions → Issues → **Read and write**
   - All other permissions: **No access**
3. Generate and copy the token
4. Add it as `VIDGET_REPORT_TOKEN` in your repo's secrets

If you prefer not to report errors automatically, skip this secret entirely.
The publish workflow prints a warning but does not fail if the token is absent.

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
