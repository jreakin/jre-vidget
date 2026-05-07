# Setup Guide

## Why three credentials?

The YouTube Data API v3 doesn't allow video uploads with just an API key. Google mandates
OAuth 2.0 for any write operation (uploads, metadata updates). Think of it this way:

| Credential | What it represents |
|------------|--------------------|
| `VIDGET_CLIENT_ID` | Which Google Cloud app is making the request |
| `VIDGET_CLIENT_SECRET` | Proof that you own that app |
| `VIDGET_REFRESH_TOKEN` | Proof that a YouTube account authorized that app to upload |

All three are required by Google — there's no "just give me an upload token" shortcut.

The `client_id` and `client_secret` for a Desktop App are not particularly sensitive.
Google acknowledges they can't truly be kept secret in an installed/local app. The real
credential is the `refresh_token` — that's what actually authorizes access to your
YouTube channel. Guard it like a password.

The setup is a **one-time process**. Once all three are in GitHub Secrets you never
touch them again unless you revoke access or Google expires the refresh token after
extended inactivity.

---

## Prerequisites

1. A Google Cloud project with **YouTube Data API v3** enabled
2. OAuth 2.0 credentials (type: **Desktop app**) — copy the client ID and secret
3. [uv](https://docs.astral.sh/uv/) installed locally for the one-time auth step

<a id="step-2"></a>

## Step 2: Google Cloud OAuth client (YouTube uploads)

Use the same credentials for the **CLI**, the **GitHub Pages setup wizard**, and **GitHub Actions** uploads.

1. Open [Google Cloud Console](https://console.cloud.google.com/) and select or create a project.
2. **APIs & Services → Library** → search **YouTube Data API v3** → **Enable**.
3. **APIs & Services → OAuth consent screen**:
   - Choose **External** (typical for personal forks) or **Internal** if you use Google Workspace.
   - Complete the required fields (app name, user support email, developer contact).
   - **Scopes** → **Add or remove scopes** → include **`https://www.googleapis.com/auth/youtube.upload`** (uploads).
   - While publishing status is **Testing**, add your own Google account under **Test users** so you can finish the browser consent during `vidget auth login`.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Application type: **Desktop app** (required: the CLI flow redirects to `localhost`, not your GitHub Pages URL).
   - Save the **Client ID** and **Client secret** — they map to GitHub Actions secrets `VIDGET_CLIENT_ID` and `VIDGET_CLIENT_SECRET`.

If you ever add a **Web application** OAuth client that runs inside the browser on GitHub Pages, set **Authorized JavaScript origins** and **Authorized redirect URIs** to your **exact** site URL (scheme, host, path, and trailing slash must match what the app uses), for example `https://YOUR_USERNAME.github.io/jre-vidget/`. The default jre-vidget flow does **not** need a Web client for uploads; it uses a Desktop client plus local `auth login`.

<a id="step-3"></a>

## Step 3: One-time OAuth flow (local)

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

### Custom OAuth callback port (`VIDGET_OAUTH_PORT`)

By default the browser OAuth flow listens on **port 8080**. If that port is already in
use (VPN software, another app, or corporate policy), set `VIDGET_OAUTH_PORT` to a free
port in **1–65535** before `uv run vidget auth login` (see `.env.example`).

**Google Cloud Console:** Desktop OAuth clients often accept loopback redirects on
multiple ports, but if consent fails after changing the port, open **APIs & Services →
Credentials → your OAuth 2.0 Client ID** and ensure **Authorized redirect URIs** include
`http://localhost:<your-port>/` (or `http://127.0.0.1:<your-port>/`) matching what the
library uses. Invalid `VIDGET_OAUTH_PORT` values are ignored with a **WARNING** in logs
and the default port is used.

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

## Web UI: GitHub PAT in the browser (risk note)

The GitHub Pages UI (`web/`) can store a **fine-grained or classic GitHub PAT** in
`localStorage` under the key `vidget_gh_pat` so the SPA can call GitHub’s REST API
(workflow dispatch, secrets, etc.) directly from the browser. The token is **never**
written to the repository; it stays on the user’s machine inside the browser profile.

**Risks to understand:**

- **XSS on the Pages origin** — any script that executes in the context of your GitHub
  Pages site could read `localStorage`. Keep the Pages site static, avoid untrusted
  third-party scripts, and use a PAT scoped to the smallest repository + permission set.
- **Shared or unlocked devices** — anyone with access to the browser profile can use or
  export the PAT until you revoke it on GitHub or clear site data (use **Clear PAT** in
  the UI when done).
- **Phishing** — only enter a PAT on your real `https://<user>.github.io/<repo>/` URL.

Prefer **fine-grained tokens** with repository-only access and the minimum permissions
the setup wizard lists. Rotate or revoke the token if it may have leaked.

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
