# YouTube Publish Feature — Design Spec

**Date:** 2026-05-03
**Status:** Approved
**Author:** jreakin

---

## Overview

Add the ability to authorize vidget against a YouTube channel and publish downloaded
videos directly — either as a one-step `vidget download URL --publish` or as a standalone
`vidget publish file.mp4` command operating on any local file.

---

## New Files

| File | Purpose |
|------|---------|
| `src/jre_vidget/auth.py` | OAuth token lifecycle — acquire, store, refresh, revoke |
| `src/jre_vidget/publisher.py` | YouTube Data API v3 wrapper — upload, progress, result |

## Modified Files

| File | Change |
|------|--------|
| `src/jre_vidget/models.py` | Add `AuthConfig`, `PublishConfig`, `PublishResult`, `AuthMode` |
| `src/jre_vidget/cli.py` | Add `auth` subcommand group, `publish` command, `--publish` flag on `download` |
| `pyproject.toml` | Add `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2` |

---

## Models (`models.py`)

```python
class AuthMode(StrEnum):
    BROWSER = "browser"
    SERVICE_ACCOUNT = "service_account"

class AuthConfig(BaseModel):
    mode: AuthMode = AuthMode.BROWSER
    client_id: str | None = None
    client_secret: str | None = None
    refresh_token: str | None = None        # persisted to ~/.vidget/config.json
    service_account_path: Path | None = None

class PublishConfig(BaseModel):
    filepath: Path
    title: str                              # defaults to VideoInfo.title
    description: str = ""
    privacy: Literal["public", "unlisted", "private"] = "public"
    remove_after_upload: bool = False

class PublishResult(BaseModel):
    video_id: str
    url: str                                # https://youtube.com/watch?v={video_id}
    title: str
    privacy: str
    removed_local_file: bool = False
```

`AuthConfig` is embedded in `AppConfig` so YouTube credentials persist to
`~/.vidget/config.json` alongside existing preferences. No separate credential file.

---

## `auth.py`

Pure credential management — no CLI, no Rich, no YouTube video data.

### Public API

```python
def login_browser(client_id: str, client_secret: str) -> AuthConfig
def login_service_account(key_path: Path) -> AuthConfig
def get_credentials(auth: AuthConfig) -> google.oauth2.credentials.Credentials
def logout() -> None
```

### Behaviour

- **`login_browser`** — starts a local HTTP server on port 8080, opens the Google OAuth
  consent URL via `webbrowser.open()`, waits for the redirect callback, exchanges the
  authorization code for tokens. Stores `refresh_token` in `AppConfig`.
- **`login_service_account`** — validates the JSON key file exists and has the correct
  shape. Stores the path in `AppConfig`; credentials are referenced, not copied.
- **`get_credentials`** — the single entry point for `publisher.py`. Returns valid,
  refreshed credentials regardless of auth mode. Handles token refresh transparently.
  Raises `AuthError` if credentials are missing or refresh fails.
- **`logout`** — clears `refresh_token` and `service_account_path` from `AppConfig`.

### OAuth Scope

`https://www.googleapis.com/auth/youtube.upload` — narrowest possible permission.

### Token Storage

`refresh_token` stored plaintext in `~/.vidget/config.json`. Consistent with how
`gh`, `gcloud`, and other CLI tools handle OAuth tokens. No keychain dependency;
works in Docker with a mounted config volume.

### Exceptions

```python
class AuthError(Exception):
    """Raised when credentials are missing, invalid, or cannot be refreshed."""
```

---

## `publisher.py`

Pure upload logic — no CLI, no Rich, no auth management. Mirrors `engine.py` in structure.

### Public API

```python
def upload(config: PublishConfig, auth: AuthConfig) -> PublishResult
```

### Upload Flow

1. Call `auth.get_credentials(auth)` — raises `AuthError` if not configured
2. Build `MediaFileUpload(filepath, resumable=True)` — handles large files (multi-GB HLS)
3. Call `youtube.videos().insert()` with:
   - `snippet.title` = `config.title`
   - `snippet.description` = `config.description`
   - `status.privacyStatus` = `config.privacy`
4. On success → return `PublishResult(video_id, url, title, privacy)`
5. If `config.remove_after_upload` → delete local file **only after** `video_id` confirmed
6. On `HttpError` → map to `PublishError` with API message + retry hint

### Resumable Uploads

`resumable=True` on `MediaFileUpload` enables chunked upload with automatic resume on
connection drop. Essential for large video files over unreliable connections.

### Progress Hook

Upload progress (bytes uploaded / total) is passed as a callback from `cli.py` — the
same pattern as `engine.py`'s `progress_hook`. `publisher.py` never imports Rich or Typer.

### Exceptions

```python
class PublishError(Exception):
    """Raised when the YouTube API rejects the upload or returns an error."""
```

---

## CLI Commands (`cli.py`)

### Auth Subcommand Group

```bash
vidget auth login                           # browser OAuth (local machine)
vidget auth login --mode service-account \
  --key /path/to/service-account.json       # service account (server/Docker)
vidget auth status                          # show connection + quota info
vidget auth logout                          # clear stored credentials
```

**`vidget auth login` (browser flow):**
- Prompts for `client_id` and `client_secret` on first run (one-time setup)
- Subsequent logins reuse stored client ID/secret; just refreshes the token
- Opens `http://localhost:8080` automatically via `webbrowser.open()`

**`vidget auth status` output:**
```
YouTube  ✓ connected  (browser · token valid)
         Channel: John Reakin · quota used today: 892 / 10,000 units
```

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
1. Run download normally → `DownloadResult`
2. If download succeeded → auto-populate `PublishConfig.title` from `VideoInfo.title`
3. Call `publisher.upload(publish_config, auth_config)`
4. Print YouTube URL on success: `✓ https://youtube.com/watch?v=abc123`
5. If `--remove` and upload succeeded → delete local file

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

Exit codes follow the semantic table in `AGENTS.md`: `3` = auth error, `4` = transient/retry.

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
    ...

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
3. Create **OAuth 2.0 credentials** (Desktop App type) → download client ID + secret
4. Run `vidget auth login` and enter the client ID and secret when prompted

For service account mode (server/Docker):
1. Create a service account in the Google Cloud project
2. Download the JSON key file
3. Run `vidget auth login --mode service-account --key /path/to/key.json`

---

## Out of Scope

- Scheduling / publishing at a future time
- Thumbnail upload
- Playlist assignment
- Editing or deleting uploaded videos
- Multi-channel support (one channel per config)
