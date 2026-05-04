# YouTube Publish Feature — Design Spec

**Date:** 2026-05-03
**Status:** Approved
**Author:** jreakin

---

## Overview

Add the ability to authorize vidget against a YouTube channel and publish downloaded
videos directly — either as a one-step `vidget download URL --publish` or as a standalone
`vidget publish file.mp4` command operating on any local file.

**V1 scope:** browser-based OAuth only (personal YouTube channels). Service account
support is deferred to V2 — the YouTube Data API v3 does not permit service accounts
to upload to standard personal/brand channels without Google Workspace domain-wide
delegation, which is out of scope here.

---

## New Files

| File | Purpose |
|------|---------|
| `src/jre_vidget/auth.py` | OAuth token lifecycle — acquire, store, refresh, revoke |
| `src/jre_vidget/publisher.py` | YouTube Data API v3 wrapper — upload, progress, result |

## Modified Files

| File | Change |
|------|--------|
| `src/jre_vidget/models.py` | Add `AuthConfig`, `PublishConfig`, `PublishResult` |
| `src/jre_vidget/cli.py` | Add `auth` subcommand group, `publish` command, `--publish` flag on `download` |
| `pyproject.toml` | Add `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2` |

---

## Models (`models.py`)

```python
class AuthConfig(BaseModel):
    client_id: str | None = None
    client_secret: str | None = None    # see Security note below
    refresh_token: str | None = None    # persisted to ~/.vidget/config.json

class PublishConfig(BaseModel):
    filepath: Path
    title: str                          # required — populated from VideoInfo.title by CLI
    description: str = ""
    privacy: Literal["public", "unlisted", "private"] = "public"
    remove_after_upload: bool = False

class PublishResult(BaseModel):
    video_id: str
    url: str                            # https://youtube.com/watch?v={video_id}
    title: str
    privacy: str
    removed_local_file: bool = False
```

`AuthConfig` is embedded in `AppConfig` so credentials persist to `~/.vidget/config.json`
alongside existing preferences.

**Security note on `client_secret`:** For OAuth "installed app" flows, the client secret
is not a high-value credential — it cannot be used to access user data without the user's
explicit consent and a valid refresh token. Google's own guidance acknowledges that
client secrets in installed apps cannot be kept truly secret. Storage in `~/.vidget/config.json`
(readable only by the file owner) is an acceptable tradeoff for a personal CLI tool,
consistent with how other personal CLI tools handle OAuth credentials. Users who want
stricter isolation can set `VIDGET_CLIENT_ID` and `VIDGET_CLIENT_SECRET` env vars — these
take precedence over the config file if set.

---

## `auth.py`

Pure credential management — no CLI, no Rich, no YouTube video data.

### Public API

```python
class AuthError(Exception):
    """Raised when credentials are missing, invalid, or cannot be refreshed."""

def login_browser(client_id: str, client_secret: str) -> AuthConfig
def get_credentials(auth: AuthConfig) -> google.oauth2.credentials.Credentials
def logout(cfg: AppConfig) -> AppConfig
```

Exceptions are caught in `cli.py` as `auth.AuthError`.

### Behaviour

- **`login_browser`** — starts a local HTTP server on port 8080, opens the Google OAuth
  consent URL via `webbrowser.open()`, waits for the redirect callback, exchanges the
  authorization code for tokens. Returns an `AuthConfig` with `refresh_token` populated.
  The caller (`cli.py`) is responsible for persisting to `AppConfig`.
- **`get_credentials`** — the single entry point for `publisher.py`. Returns valid,
  refreshed credentials. Handles token refresh transparently using the stored
  `refresh_token`. Raises `AuthError` if credentials are missing or refresh fails.
- **`logout(cfg)`** — clears `client_id`, `client_secret`, and `refresh_token` from the
  passed `AppConfig`, calls `cfg.save()`, and returns the updated config.

### OAuth Scope

`https://www.googleapis.com/auth/youtube.upload` — narrowest possible permission.

### Token Storage

`refresh_token` stored in `~/.vidget/config.json`. `client_id` and `client_secret` can
alternatively be provided via `VIDGET_CLIENT_ID` / `VIDGET_CLIENT_SECRET` environment
variables, which take precedence over the config file.

---

## `publisher.py`

Pure upload logic — no CLI, no Rich, no auth management. Mirrors `engine.py` in structure.

### Public API

```python
class PublishError(Exception):
    """Raised when the YouTube API rejects the upload or returns an error."""

UploadProgressHook = Callable[[int, int], None]  # (bytes_uploaded, total_bytes)

def upload(
    config: PublishConfig,
    auth: AuthConfig,
    progress_hook: UploadProgressHook | None = None,
) -> PublishResult
```

Exceptions are caught in `cli.py` as `publisher.PublishError`.

### Upload Flow

1. Call `auth.get_credentials(auth)` — raises `AuthError` if not configured
2. Build `MediaFileUpload(config.filepath, resumable=True)` using `httplib2` transport
3. Call `youtube.videos().insert()` with:
   - `snippet.title` = `config.title`
   - `snippet.description` = `config.description`
   - `status.privacyStatus` = `config.privacy`
4. During chunked upload, call `progress_hook(bytes_uploaded, total_bytes)` after each chunk
   if `progress_hook` is not None
5. On success → return `PublishResult(video_id, url, title, privacy)`
6. If `config.remove_after_upload` → delete local file **only after** `video_id` confirmed
7. On `HttpError` → map to `PublishError` with API message + retry hint

### Resumable Uploads

`resumable=True` on `MediaFileUpload` enables chunked upload with automatic resume on
connection drop. Essential for large video files (multi-GB HLS clips).

### HTTP Transport

Use `httplib2` (via `google-auth-httplib2`) — the conventional default for
`google-api-python-client`. Do not use the `requests` transport.

---

## CLI Commands (`cli.py`)

### Auth Subcommand Group

```bash
vidget auth login                           # browser OAuth
vidget auth status                          # show connection + channel info
vidget auth logout                          # clear stored credentials
```

**`vidget auth login` (browser flow):**
- Prompts for `client_id` and `client_secret` on first run (one-time setup)
- Subsequent logins reuse stored client ID/secret; just refreshes the token
- Opens `http://localhost:8080` automatically via `webbrowser.open()`

**`vidget auth status` output:**
```
YouTube  ✓ connected  (token valid)
         Channel: John Reakin
```

Note: YouTube API quota is not queryable via the Data API v3 — quota display is omitted.

### Publish Command

```bash
vidget publish ./downloads/video.mp4
vidget publish ./downloads/video.mp4 \
  --title "My Custom Title" \
  --description "Posted from vidget" \
  --privacy unlisted \
  --remove
```

### Download + Publish Flag

```bash
vidget download "URL" --publish
vidget download "URL" --publish --title "Override" --privacy private --remove
```

**Flow when `--publish` is set:**
1. Call `engine.fetch_info(url)` → `VideoInfo` (gets title before download starts)
2. Run `engine.download(config)` normally → `DownloadResult`
3. If download succeeded → build `PublishConfig(title=video_info.title, ...)`,
   override title if `--title` was passed explicitly
4. Call `publisher.upload(publish_config, auth_config, progress_hook)`
5. Print YouTube URL on success: `✓ https://youtube.com/watch?v=abc123`
6. If `--remove` and upload succeeded → delete local file
   (`--remove` applies only to the upload step, not the download step)

---

## Error Handling

| Error | Exit Code | User Message |
|-------|-----------|-------------|
| Not authenticated | `3` | `"Run 'vidget auth login' to connect your YouTube account."` |
| Token expired, refresh failed | `3` | `"YouTube session expired. Run 'vidget auth login'."` |
| Quota exceeded | `4` | `"YouTube quota exceeded. Try again after midnight Pacific."` |
| File not found | `1` | `"File not found: {path}"` |
| API rejection | `1` | YouTube API message surfaced directly |
| Upload interrupted | `4` | `"Upload interrupted — safe to retry (resumable)."` |

Exit codes follow the semantic table in `AGENTS.md` → Agentic CLI Design Principles section.

---

## Dependencies

```toml
# pyproject.toml — add to [project.dependencies]
"google-api-python-client>=2.100",
"google-auth-oauthlib>=1.2",
"google-auth-httplib2>=0.2",
```

---

## Testing Strategy

Mock at the Google API boundary — no real YouTube API calls in tests.

```python
# Unit — publisher.py
with patch("jre_vidget.publisher.build") as mock_build:
    mock_build.return_value.videos().insert().execute.return_value = {"id": "abc123"}
    result = publisher.upload(config, auth)
    assert result.video_id == "abc123"
    assert result.url == "https://youtube.com/watch?v=abc123"

# Unit — auth.py
with patch("jre_vidget.auth.InstalledAppFlow") as mock_flow:
    mock_flow.from_client_config.return_value.run_local_server.return_value = mock_creds
    auth_config = auth.login_browser("client_id", "client_secret")
    assert auth_config.refresh_token is not None

# Integration — CLI
with patch("jre_vidget.cli.publisher.upload") as mock_upload:
    mock_upload.return_value = PublishResult(video_id="abc123", ...)
    result = runner.invoke(app, ["publish", str(tmp_path / "video.mp4")])
    assert result.exit_code == 0
```

Coverage target: ≥ 80% on `auth.py` and `publisher.py`, consistent with existing modules.

---

## Prerequisites (User Setup)

Before running `vidget auth login`, the user must:

1. Create a Google Cloud project at [console.cloud.google.com](https://console.cloud.google.com)
2. Enable the **YouTube Data API v3**
3. Create **OAuth 2.0 credentials** (type: Desktop App) → copy Client ID and Client Secret
4. Run `vidget auth login` → enter Client ID and Client Secret when prompted

---

## Out of Scope (V1)

- Service account auth (requires Google Workspace — deferred to V2)
- Scheduling / publishing at a future time
- Thumbnail upload
- Playlist assignment
- Editing or deleting uploaded videos
- Multi-channel support (one channel per config)
